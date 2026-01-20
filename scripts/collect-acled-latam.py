#!/usr/bin/env python3
"""
ACLED Latin America Collector (Targeted)
"""
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import pandas as pd
import psycopg2
from psycopg2.extras import Json, execute_values
from pathlib import Path
from datetime import datetime, timezone
import time
import logging
from typing import Dict, Optional, List, Tuple
import sys
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Credentials
EMAIL = os.getenv("ACLED_EMAIL")
PASSWORD = os.getenv("ACLED_PASSWORD")
if not EMAIL or not PASSWORD:
    print("❌ ERROR: ACLED_EMAIL and ACLED_PASSWORD required")
    sys.exit(1)

# PostgreSQL
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

# Paths
BASE_DIR = Path("data/acled")
RAW_DIR = BASE_DIR / "raw"
DEBUG_DIR = BASE_DIR / "debug"

# Dataset
DATASETS = [
    {"slug": "aggregated-latin-america-caribbean", "url": "https://acleddata.com/aggregated/aggregated-data-latin-america-caribbean", "aggregation_level": "regional", "region": "Latin America and Caribbean"}
]

TIMEOUT = 30

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Simplified Helper Functions from V3 ---

def calculate_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def to_snake_case(name: str) -> str:
    return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').strip()

def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    logger.info("Authenticating...")
    r = session.get("https://acleddata.com/user/login", timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, 'html.parser')
    form = soup.find('form', {'id': 'user-login-form'})
    if not form: raise Exception("Login form not found")
    
    payload = {inp['name']: inp.get('value', '') for inp in form.find_all('input') if inp.get('name')}
    payload['name'] = EMAIL
    payload['pass'] = PASSWORD
    payload.setdefault('op', 'Log in')
    
    action = form.get('action')
    if not action.startswith('http'): action = "https://acleddata.com" + action
    
    session.post(action, data=payload, timeout=TIMEOUT)
    if any(n.startswith('SSESS') for n in session.cookies.keys()):
        logger.info("✅ Authenticated")
        return session
    raise Exception("Authentication failed")

def find_download_link(session: requests.Session, url: str) -> Optional[dict]:
    r = session.get(url, timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        if any(ext in href.lower() for ext in ['.xlsx', '.csv', '/wp-content/uploads/']):
            if not href.startswith('http'): href = "https://acleddata.com" + href
            return {"url": href, "strategy": "A"}
    return None

def insert_regional(conn, df: pd.DataFrame, slug: str, hash: str, region: str):
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]
    df = df.where(pd.notna(df), None)
    
    records = []
    for _, row in df.iterrows():
        week_str = None
        year_val = None
        month_val = None
        if row.get('week'):
            dt = pd.to_datetime(row['week'])
            year_val = int(dt.year)
            month_val = int(dt.month)
            week_str = int(dt.isocalendar().week)
            
        metadata = {k: (v.isoformat() if isinstance(v, (pd.Timestamp, datetime)) else v) 
                   for k, v in row.items() if k not in ['country', 'events', 'fatalities', 'week', 'year', 'month']}

        records.append((
            slug, region, row.get('country'), row.get('admin1'), row.get('admin2'),
            year_val, month_val, week_str,
            None, None,
            float(row['centroid_latitude']) if row.get('centroid_latitude') else None,
            float(row['centroid_longitude']) if row.get('centroid_longitude') else None,
            int(row['events']) if row.get('events') else 0,
            int(row['fatalities']) if row.get('fatalities') else 0,
            row.get('event_type'), row.get('disorder_type'),
            Json(metadata), hash, datetime.now(timezone.utc)
        ))
        
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.regional (
                dataset_slug, region, country, admin1, admin2, year, month, week, date_range_start, date_range_end,
                centroid_latitude, centroid_longitude, events, fatalities, event_type, disorder_type, metadata,
                source_file_hash, collected_at
            ) VALUES %s ON CONFLICT DO NOTHING
        """, records)
    conn.commit()
    # conn.commit() # Removed due to autocommit
    logger.info(f"Inserted {len(records)} rows")

def main():
    try:
        session = create_session()
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True  # CRITICAL: Enable autocommit
        
        for ds in DATASETS:
            logger.info(f"Processing {ds['slug']}...")
            link = find_download_link(session, ds['url'])
            if not link:
                logger.error("No link found")
                continue
                
            logger.info(f"Downloading {link['url']}...")
            r = session.get(link['url'])
            file_name = f"temp_latam.xlsx"
            with open(file_name, 'wb') as f:
                f.write(r.content)
            
            df = pd.read_excel(file_name)
            logger.info(f"Loaded {len(df)} rows")
            
            insert_regional(conn, df, ds['slug'], "manual_run", ds['region'])
            logger.info("✅ Done - data persisted")
            
            if os.path.exists(file_name): os.remove(file_name)
        
        conn.close()
        logger.info("✅ ALL COMPLETE")
            
    except Exception as e:
        import traceback
        logger.error(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
