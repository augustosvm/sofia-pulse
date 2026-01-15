#!/usr/bin/env python3
"""
ACLED Aggregated Data Collector - PostgreSQL Pipeline
======================================================
Collects OFFICIAL aggregated datasets from ACLED and stores them in PostgreSQL.

CRITICAL: These are NOT derived from event-level data.
          These are OFFICIAL published aggregates that must be ingested directly.

Author: Sofia Pulse Team  
Date: 2026-01-15
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

# ============================================================================
# Configuration
# ============================================================================

# Login credentials
EMAIL = os.getenv("ACLED_EMAIL", "augusto@tiespecialistas.com.br")
PASSWORD = os.getenv("ACLED_PASSWORD", "75August!@")

# PostgreSQL configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "91.98.158.19"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", "SofiaPulse2025Secure@DB"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

#Base paths
BASE_DIR = Path("data/acled")
RAW_DIR = BASE_DIR / "raw"

# Request configuration
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2

# Dataset definitions
DATASETS = [
    {"slug": "political-violence-country-year", "url": "https://acleddata.com/aggregated/number-political-violence-events-country-year", "aggregation_level": "country-year", "region": "Global"},
    {"slug": "political-violence-country-month-year", "url": "https://acleddata.com/aggregated/number-political-violence-events-country-month-year", "aggregation_level": "country-month-year", "region": "Global"},
    {"slug": "demonstrations-country-year", "url": "https://acleddata.com/aggregated/number-demonstration-events-country-year", "aggregation_level": "country-year", "region": "Global"},
    {"slug": "civilian-targeting-country-year", "url": "https://acleddata.com/aggregated/number-events-targeting-civilians-country-year", "aggregation_level": "country-year", "region": "Global"},
    {"slug": "fatalities-country-year", "url": "https://acleddata.com/aggregated/number-reported-fatalities-country-year", "aggregation_level": "country-year", "region": "Global"},
    {"slug": "civilian-fatalities-country-year", "url": "https://acleddata.com/aggregated/number-reported-civilian-fatalities-direct-targeting-country-year", "aggregation_level": "country-year", "region": "Global"},
    {"slug": "aggregated-europe-central-asia", "url": "https://acleddata.com/aggregated/aggregated-data-europe-and-central-asia", "aggregation_level": "regional", "region": "Europe and Central Asia"},
    {"slug": "aggregated-us-canada", "url": "https://acleddata.com/aggregated/aggregated-data-united-states-canada", "aggregation_level": "regional", "region": "United States and Canada"},
    {"slug": "aggregated-latin-america-caribbean", "url": "https://acleddata.com/aggregated/aggregated-data-latin-america-caribbean", "aggregation_level": "regional", "region": "Latin America and Caribbean"},
    {"slug": "aggregated-middle-east", "url": "https://acleddata.com/aggregated/aggregated-data-middle-east", "aggregation_level": "regional", "region": "Middle East"},
    {"slug": "aggregated-asia-pacific", "url": "https://acleddata.com/aggregated/aggregated-data-asia-pacific", "aggregation_level": "regional", "region": "Asia Pacific"},
    {"slug": "aggregated-africa", "url": "https://acleddata.com/aggregated/aggregated-data-africa", "aggregation_level": "regional", "region": "Africa"}
]

# ============================================================================
# Setup Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('acled_aggregated_postgres.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def to_snake_case(name: str) -> str:
    """Convert column name to snake_case."""
    return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').strip()


def detect_aggregation_type(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Detect if dataset is aggregated and determine the aggregation level.
    Returns: (aggregation_level, target_table)
    """
    columns_lower = [col.lower() for col in df.columns]
    
    # Classify as AGGREGATED if:
    # - Has "events" or "fatalities" as count columns
    # - Has temporal columns (year, month, week)
    # - Does NOT have event-level columns
    
    has_events = 'events' in columns_lower or 'fatalities' in columns_lower
    has_temporal = any(t in columns_lower for t in ['year', 'month', 'week'])
    has_geo = any(g in columns_lower for g in ['country', 'admin1', 'region'])
    
    # Event-level indicators (should NOT be present)
    event_indicators = ['event_date', 'actor1', 'actor2', 'latitude', 'longitude', 'event_id']
    has_event_level = any(e in columns_lower for e in event_indicators)
    
    if not has_events or has_event_level:
        logger.warning("Dataset does NOT appear to be aggregated!")
        return ("unknown", "unknown")
    
    # Determine granularity
    if 'year' in columns_lower and 'month' in columns_lower:
        return ("country-month-year", "acled_aggregated.country_month_year")
    elif 'year' in columns_lower and 'country' in columns_lower:
        return ("country-year", "acled_aggregated.country_year")
    elif 'week' in columns_lower or 'admin1' in columns_lower:
        return ("regional", "acled_aggregated.regional")
    else:
        return ("country-year", "acled_aggregated.country_year")  # default


def create_session() -> requests.Session:
    """Create and authenticate a session with ACLED."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://acleddata.com"
    })
    
    logger.info("Authenticating with ACLED...")
    
    r = session.get("https://acleddata.com/user/login", timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    form = soup.find('form', {'id': 'user-login-form'})
    if not form:
        raise Exception("Login form not found")
    
    action = form.get('action')
    if not action.startswith('http'):
        action = "https://acleddata.com" + action
    
    payload = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        value = inp.get('value', '')
        if name:
            payload[name] = value
    
    payload['name'] = EMAIL
    payload['pass'] = PASSWORD
    if 'op' not in payload:
        payload['op'] = 'Log in'
    
    r_login = session.post(action, data=payload, timeout=TIMEOUT)
    
    cookie_names = list(session.cookies.keys())
    has_session = any(name.startswith('SSESS') for name in cookie_names)
    
    if has_session:
        logger.info("✅ Authentication successful")
        return session
    else:
        raise Exception("Authentication failed")


def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def find_download_link(session: requests.Session, page_url: str) -> Optional[str]:
    """Find the download link on an ACLED aggregated data page."""
    try:
        r = session.get(page_url, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(ext in href.lower() for ext in ['.xlsx', '.csv', '.zip']):
                if not href.startswith('http'):
                    href = 'https://acleddata.com' + href
                logger.info(f"Found download link: {href}")
                return href
        
        return None
    except Exception as e:
        logger.error(f"Error finding download link: {e}")
        return None


def save_metadata(conn, dataset: Dict, file_info: Dict):
    """Save or update metadata in PostgreSQL."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO acled_metadata.datasets (
                dataset_slug, source_url, download_url, aggregation_level, region,
                file_hash, file_name, file_size_bytes, collected_at, is_aggregated,
                source_type, detected_columns, version_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, 'ACLED_OFFICIAL_AGGREGATE', %s, %s)
            ON CONFLICT (dataset_slug) DO UPDATE SET
                download_url = EXCLUDED.download_url,
                file_hash = EXCLUDED.file_hash,
                file_name = EXCLUDED.file_name,
                file_size_bytes = EXCLUDED.file_size_bytes,
                collected_at = EXCLUDED.collected_at,
                detected_columns = EXCLUDED.detected_columns,
                version_date = EXCLUDED.version_date,
                updated_at = NOW()
        """, (
            dataset['slug'],
            dataset['url'],
            file_info['download_url'],
            file_info['aggregation_level'],
            dataset.get('region'),
            file_info['file_hash'],
            file_info['file_name'],
            file_info['file_size'],
            datetime.now(timezone.utc),
            Json(file_info.get('columns', [])),
            file_info.get('version_date')
        ))
    conn.commit()
    logger.info("Metadata saved to PostgreSQL")


def insert_to_country_year(conn, df: pd.DataFrame, dataset_slug: str, file_hash: str):
    """Insert data into country_year table."""
    df_clean = df.copy()
    df_clean.columns = [to_snake_case(col) for col in df_clean.columns]
    
    # Map expected columns
    records = []
    for _, row in df_clean.iterrows():
        record = {
            'dataset_slug': dataset_slug,
            'country': row.get('country', ''),
            'year': int(row.get('year', 0)) if pd.notna(row.get('year')) else None,
            'events': int(row.get('events', 0)) if pd.notna(row.get('events')) else None,
            'fatalities': int(row.get('fatalities')) if 'fatalities' in row and pd.notna(row.get('fatalities')) else None,
            'metadata': Json({k: v for k, v in row.items() if k not in ['country', 'year', 'events', 'fatalities']}),
            'source_file_hash': file_hash,
            'collected_at': datetime.now(timezone.utc)
        }
        records.append(record)
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.country_year (
                dataset_slug, country, year, events, fatalities, metadata, source_file_hash, collected_at
            ) VALUES %s
            ON CONFLICT (dataset_slug, country, year, source_file_hash) DO NOTHING
        """, [(r['dataset_slug'], r['country'], r['year'], r['events'], r['fatalities'], r['metadata'], r['source_file_hash'], r['collected_at']) for r in records])
    
    conn.commit()
    logger.info(f"Inserted {len(records)} records into country_year")


def insert_to_country_month_year(conn, df: pd.DataFrame, dataset_slug: str, file_hash: str):
    """Insert data into country_month_year table."""
    df_clean = df.copy()
    df_clean.columns = [to_snake_case(col) for col in df_clean.columns]
    
    records = []
    for _, row in df_clean.iterrows():
        record = (
            dataset_slug,
            row.get('country', ''),
            int(row.get('year', 0)) if pd.notna(row.get('year')) else None,
            int(row.get('month', 0)) if pd.notna(row.get('month')) else None,
            int(row.get('events', 0)) if pd.notna(row.get('events')) else None,
            int(row.get('fatalities')) if 'fatalities' in row and pd.notna(row.get('fatalities')) else None,
            Json({k: v for k, v in row.items() if k not in ['country', 'year', 'month', 'events', 'fatalities']}),
            file_hash,
            datetime.now(timezone.utc)
        )
        records.append(record)
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.country_month_year (
                dataset_slug, country, year, month, events, fatalities, metadata, source_file_hash, collected_at
            ) VALUES %s
            ON CONFLICT (dataset_slug, country, year, month, source_file_hash) DO NOTHING
        """, records)
    
    conn.commit()
    logger.info(f"Inserted {len(records)} records into country_month_year")


def insert_to_regional(conn, df: pd.DataFrame, dataset_slug: str, file_hash: str, region: str):
    """Insert data into regional table."""
    df_clean = df.copy()
    df_clean.columns = [to_snake_case(col) for col in df_clean.columns]
    
    records = []
    for _, row in df_clean.iterrows():
        record = (
            dataset_slug,
            region,
            row.get('country'),
            row.get('admin1'),
            int(row.get('year')) if 'year' in row and pd.notna(row.get('year')) else None,
            int(row.get('month')) if 'month' in row and pd.notna(row.get('month')) else None,
            int(row.get('week')) if 'week' in row and pd.notna(row.get('week')) else None,
            None,  # date_range_start
            None,  # date_range_end
            int(row.get('events', 0)) if pd.notna(row.get('events')) else None,
            int(row.get('fatalities')) if 'fatalities' in row and pd.notna(row.get('fatalities')) else None,
            row.get('event_type'),
            Json({k: v for k, v in row.items() if k not in ['country', 'admin1', 'year', 'month', 'week', 'events', 'fatalities', 'event_type']}),
            file_hash,
            datetime.now(timezone.utc)
        )
        records.append(record)
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.regional (
                dataset_slug, region, country, admin1, year, month, week, date_range_start, date_range_end,
                events, fatalities, event_type, metadata, source_file_hash, collected_at
            ) VALUES %s
            ON CONFLICT (dataset_slug, region, country, admin1, year, month, week, event_type, source_file_hash) DO NOTHING
        """, records)
    
    conn.commit()
    logger.info(f"Inserted {len(records)} records into regional")


def collect_dataset(session: requests.Session, conn, dataset: Dict) -> bool:
    """Collect a single dataset and store in PostgreSQL."""
    slug = dataset['slug']
    url = dataset['url']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing: {slug}")
    logger.info(f"{'='*70}")
    
    try:
        # Find download link
        download_url = find_download_link(session, url)
        if not download_url:
            logger.error(f"No download link found")
            return False
        
        # Download file
        file_name = download_url.split('/')[-1].split('?')[0]
        logger.info(f"Downloading {file_name}...")
        
        response = session.get(download_url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
        
        temp_file = Path(f"temp_{file_name}")
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = temp_file.stat().st_size
        file_hash = calculate_file_hash(temp_file)
        logger.info(f"Downloaded {file_size:,} bytes, hash: {file_hash[:16]}...")
        
        # Load into pandas
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(temp_file)
        elif file_name.endswith('.csv'):
            df = pd.read_csv(temp_file)
        else:
            logger.error(f"Unsupported file type: {file_name}")
            temp_file.unlink()
            return False
        
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Detect aggregation type
        agg_level, target_table = detect_aggregation_type(df)
        logger.info(f"Detected aggregation: {agg_level} → {target_table}")
        
        # Save metadata
        file_info = {
            'download_url': download_url,
            'file_name': file_name,
            'file_size': file_size,
            'file_hash': file_hash,
            'aggregation_level': agg_level,
            'columns': list(df.columns),
            'version_date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
        }
        save_metadata(conn, dataset, file_info)
        
        # Insert into appropriate table
        if target_table == "acled_aggregated.country_year":
            insert_to_country_year(conn, df, slug, file_hash)
        elif target_table == "acled_aggregated.country_month_year":
            insert_to_country_month_year(conn, df, slug, file_hash)
        elif target_table == "acled_aggregated.regional":
            insert_to_regional(conn, df, slug, file_hash, dataset.get('region', 'Unknown'))
        
        # Clean up
        temp_file.unlink()
        
        logger.info(f"✅ Successfully collected and stored: {slug}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to collect {slug}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    logger.info("="*70)
    logger.info("ACLED Aggregated Data Collector - PostgreSQL Pipeline")
    logger.info("="*70)
    logger.info(f"Datasets to collect: {len(DATASETS)}")
    
    # Create session
    try:
        session = create_session()
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return
    
    # Connect to PostgreSQL
    try:
        conn = get_db_connection()
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return
    
    # Collect datasets
    results = {'success': 0, 'failed': 0}
    
    for dataset in DATASETS:
        success = collect_dataset(session, conn, dataset)
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        time.sleep(2)  # Polite delay
    
    conn.close()
    
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"✅ Success: {results['success']}")
    logger.info(f"❌ Failed: {results['failed']}")


if __name__ == "__main__":
    main()
