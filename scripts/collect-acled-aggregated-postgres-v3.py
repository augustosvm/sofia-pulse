#!/usr/bin/env python3
"""
ACLED Aggregated Data Collector v3 - Production Grade
======================================================
Complete production pipeline with failure tracking, 4-strategy scraping,
and comprehensive audit trail.

Author: Sofia Pulse Team
Version: 3.0 (Production Complete)
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
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

# Credentials (REQUIRED via environment)
EMAIL = os.getenv("ACLED_EMAIL")
PASSWORD = os.getenv("ACLED_PASSWORD")

if not EMAIL or not PASSWORD:
    print("❌ ERROR: ACLED_EMAIL and ACLED_PASSWORD required")
    print("Set them: export ACLED_EMAIL='...' ACLED_PASSWORD='...'")
    sys.exit(1)

# PostgreSQL
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

if not DB_CONFIG["password"]:
    print("❌ ERROR: POSTGRES_PASSWORD required")
    sys.exit(1)

# Paths
BASE_DIR = Path("data/acled")
RAW_DIR = BASE_DIR / "raw"
DEBUG_DIR = BASE_DIR / "debug"

# Request config
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2
POLITE_DELAY = 2  # seconds between datasets

# Datasets - ONLY REGIONAL (country-level already collected)
DATASETS = [
    # SKIP: Already collected successfully
    # {"slug": "political-violence-country-year", ...},
    # {"slug": "political-violence-country-month-year", ...},  # Failed: month parsing
    # {"slug": "demonstrations-country-year", ...},
    # {"slug": "civilian-targeting-country-year", ...},
    # {"slug": "fatalities-country-year", ...},
    # {"slug": "civilian-fatalities-country-year", ...},

    # REGIONAL ONLY:
    {"slug": "aggregated-europe-central-asia", "url": "https://acleddata.com/aggregated/aggregated-data-europe-and-central-asia", "aggregation_level": "regional", "region": "Europe and Central Asia"},
    {"slug": "aggregated-us-canada", "url": "https://acleddata.com/aggregated/aggregated-data-united-states-canada", "aggregation_level": "regional", "region": "United States and Canada"},
    {"slug": "aggregated-latin-america-caribbean", "url": "https://acleddata.com/aggregated/aggregated-data-latin-america-caribbean", "aggregation_level": "regional", "region": "Latin America and Caribbean"},
    {"slug": "aggregated-middle-east", "url": "https://acleddata.com/aggregated/aggregated-data-middle-east", "aggregation_level": "regional", "region": "Middle East"},
    {"slug": "aggregated-asia-pacific", "url": "https://acleddata.com/aggregated/aggregated-data-asia-pacific", "aggregation_level": "regional", "region": "Asia Pacific"},
    {"slug": "aggregated-africa", "url": "https://acleddata.com/aggregated/aggregated-data-africa", "aggregation_level": "regional", "region": "Africa"}
]

# ============================================================================
# Logging with Sanitization
# ============================================================================

class SanitizingFilter(logging.Filter):
    PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password=***'),
        (r'SSESS[a-f0-9]+', 'SSESS***'),
        (r'Bearer\s+[\w\-\.\_\~\+\/]+=*', 'Bearer ***'),
    ]
    
    def filter(self, record):
        msg = record.getMessage()
        for pattern, repl in self.PATTERNS:
            msg = re.sub(pattern, repl, msg, flags=re.I)
        record.msg = msg
        record.args = ()
        return True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('acled_collector_v3.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.addFilter(SanitizingFilter())

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def to_snake_case(name: str) -> str:
    return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').strip()

def is_official_aggregate(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate official aggregate (flexible v3)."""
    cols_lower = [col.lower() for col in df.columns]
    
    # Event-level indicators (reject)
    event_indicators = ['event_date', 'event_id', 'data_id', 'actor1', 'actor2',
                        'assoc_actor_1', 'inter1', 'source', 'notes']
    
    # Check for event-specific lat/lon (not centroid)
    has_event_geo = ('latitude' in cols_lower and 'longitude' in cols_lower and 
                     'centroid_latitude' not in cols_lower)
    
    found_event = [i for i in event_indicators if i in cols_lower]
    if found_event or has_event_geo:
        return False, f"Event-level detected: {found_event or 'lat/lon'}"
    
    # Aggregate metric indicators (flexible)
    metric_indicators = ['events', 'fatalities', 'exposure', 'population_exposure',
                         'disorder_type_counts', 'event_count', 'fatality_count',
                         'civilian_fatalities', 'demonstrations']
    has_metric = any(m in cols_lower for m in metric_indicators)
    
    # Temporal aggregation
    has_temporal = any(t in cols_lower for t in ['year', 'month', 'week'])
    
    # Geo aggregation
    has_geo = any(g in cols_lower for g in ['country', 'admin1', 'admin2', 'region'])
    
    if not has_metric:
        return False, "No aggregate metric column found"
    if not has_temporal:
        return False, "No temporal aggregation column"
    if not has_geo:
        return False, "No geographic grouping column"
    
    return True, "Valid official aggregate"

def detect_granularity(df: pd.DataFrame) -> Tuple[str, str]:
    """Detect aggregation level (fixed v3)."""
    cols_lower = [col.lower() for col in df.columns]
    
    # Priority 1: Regional indicators
    if any(c in cols_lower for c in ['admin1', 'admin2', 'week', 'centroid_latitude']):
        return ("regional", "acled_aggregated.regional")
    
    # Priority 2: Country-month-year
    if all(c in cols_lower for c in ['country', 'year', 'month']):
        return ("country-month-year", "acled_aggregated.country_month_year")
    
    # Priority 3: Country-year
    if 'country' in cols_lower and 'year' in cols_lower:
        return ("country-year", "acled_aggregated.country_year")
    
    # Fallback
    return ("regional", "acled_aggregated.regional")

def save_debug(slug: str, html: str, status: int, url: str, links: List[str]):
    """Save debug HTML and link list."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    
    html_file = DEBUG_DIR / f"{slug}-{ts}.html"
    sanitized = re.sub(r'SSESS[a-f0-9]+', 'SSESS***', html)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(f"<!-- Status: {status} | URL: {url} -->\n\n{sanitized}")
    
    links_file = DEBUG_DIR / f"{slug}-{ts}-links.json"
    with open(links_file, 'w') as f:
        json.dump({"status": status, "url": url, "candidate_links": links}, f, indent=2)
    
    logger.info(f"Debug saved: {html_file.name}, {links_file.name}")

def create_session() -> requests.Session:
    """Authenticate with ACLED."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://acleddata.com"
    })
    
    logger.info("Authenticating...")
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
        if inp.get('name'):
            payload[inp['name']] = inp.get('value', '')
    
    payload['name'] = EMAIL
    payload['pass'] = PASSWORD
    payload.setdefault('op', 'Log in')
    
    r_login = session.post(action, data=payload, timeout=TIMEOUT)
    
    if any(n.startswith('SSESS') for n in session.cookies.keys()):
        logger.info("✅ Authenticated")
        return session
    raise Exception("Authentication failed")

def get_db() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CONFIG)

def find_download_link(session: requests.Session, url: str) -> Optional[Dict]:
    """4-strategy link discovery."""
    try:
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        all_links = []
        
        # STRATEGY A: Direct file links
        logger.info("Strategy A: Direct file links")
        for a in soup.find_all('a', href=True):
            href = a['href']
            all_links.append(href)
            if any(ext in href.lower() for ext in ['.xlsx', '.csv', '.zip', '/wp-content/uploads/']):
                href = href if href.startswith('http') else f"https://acleddata.com{href}"
                logger.info(f"✅ Strategy A: {href}")
                return {"url": href, "strategy": "A", "final_url": href}
        
        # STRATEGY B: Download buttons
        logger.info("Strategy B: Download buttons/links")
        for elem in soup.find_all(['a', 'button']):
            text = elem.get_text().lower()
            if any(kw in text for kw in ['download', 'export', 'xlsx', 'csv']):
                href = elem.get('href') or elem.get('data-href')
                if href:
                    href = href if href.startswith('http') else f"https://acleddata.com{href}"
                    logger.info(f"✅ Strategy B: {href}")
                    return {"url": href, "strategy": "B", "final_url": href}
        
        # STRATEGY C: Content-Type check
        logger.info("Strategy C: Content-Type check")
        for href in set(all_links[:50]):  # Limit to avoid spam
            if not href.startswith(('http', '/')):
                continue
            href = href if href.startswith('http') else f"https://acleddata.com{href}"
            try:
                head = session.head(href, timeout=5, allow_redirects=True)
                ct = head.headers.get('Content-Type', '').lower()
                if any(t in ct for t in ['xlsx', 'csv', 'spreadsheet', 'octet-stream']):
                    logger.info(f"✅ Strategy C: {head.url} (CT: {ct})")
                    return {"url": href, "strategy": "C", "final_url": head.url}
            except:
                continue
        
        # STRATEGY D: WordPress pattern
        logger.info("Strategy D: WordPress pattern")
        patterns = [r'(https?://[^\s"\']+\.xlsx)', r'(https?://[^\s"\']+\.csv)']
        for pattern in patterns:
            match = re.search(pattern, r.text, re.I)
            if match:
                href = match.group(1)
                logger.info(f"✅ Strategy D: {href}")
                return {"url": href, "strategy": "D", "final_url": href}
        
        logger.warning("❌ No link found with any strategy")
        save_debug(url.split('/')[-1], r.text, r.status_code, r.url, all_links[:100])
        return None
        
    except Exception as e:
        logger.error(f"Link discovery error: {e}")
        return None

def save_metadata(conn, dataset: Dict, status: str, error_msg: Optional[str] = None,
                  http_status: Optional[int] = None, strategy: Optional[str] = None,
                  file_info: Optional[Dict] = None):
    """Save collection attempt (success or failure)."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO acled_metadata.datasets (
                dataset_slug, source_url, download_url, download_url_final,
                aggregation_level, region, file_hash, file_name, file_size_bytes,
                collected_at, is_aggregated, source_type, detected_columns,
                version_date, status, error_message, http_status, strategy_used
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dataset['slug'], dataset['url'],
            file_info.get('download_url') if file_info else None,
            file_info.get('download_url_final') if file_info else None,
            file_info.get('aggregation_level') if file_info else None,
            dataset.get('region'),
            file_info.get('file_hash') if file_info else None,
            file_info.get('file_name') if file_info else None,
            file_info.get('file_size') if file_info else None,
            datetime.now(timezone.utc),
            file_info.get('is_aggregated') if file_info else None,
            'ACLED_OFFICIAL_AGGREGATE' if status == 'success' else 'ACLED_UNVALIDATED',
            Json(file_info.get('columns', [])) if file_info else None,
            file_info.get('version_date') if file_info else None,
            status, error_msg, http_status, strategy
        ))
    conn.commit()

def insert_country_year(conn, df: pd.DataFrame, slug: str, hash: str):
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]
    records = []
    for _, row in df.iterrows():
        records.append((
            slug, row.get('country', ''),
            int(row['year']) if pd.notna(row.get('year')) else None,
            int(row['events']) if 'events' in row and pd.notna(row['events']) else None,
            int(row['fatalities']) if 'fatalities' in row and pd.notna(row['fatalities']) else None,
            Json({k: v for k, v in row.items() if k not in ['country', 'year', 'events', 'fatalities']}),
            hash, datetime.now(timezone.utc)
        ))
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.country_year (dataset_slug, country, year, events, fatalities, metadata, source_file_hash, collected_at)
            VALUES %s ON CONFLICT DO NOTHING
        """, records)
    conn.commit()
    logger.info(f"Inserted {len(records)} rows → country_year")

def insert_country_month_year(conn, df: pd.DataFrame, slug: str, hash: str):
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]
    records = []
    for _, row in df.iterrows():
        records.append((
            slug, row.get('country', ''),
            int(row['year']) if pd.notna(row.get('year')) else None,
            int(row['month']) if pd.notna(row.get('month')) else None,
            int(row['events']) if 'events' in row and pd.notna(row['events']) else None,
            int(row['fatalities']) if 'fatalities' in row and pd.notna(row['fatalities']) else None,
            Json({k: v for k, v in row.items() if k not in ['country', 'year', 'month', 'events', 'fatalities']}),
            hash, datetime.now(timezone.utc)
        ))
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.country_month_year (dataset_slug, country, year, month, events, fatalities, metadata, source_file_hash, collected_at)
            VALUES %s ON CONFLICT DO NOTHING
        """, records)
    conn.commit()
    logger.info(f"Inserted {len(records)} rows → country_month_year")

def insert_regional(conn, df: pd.DataFrame, slug: str, hash: str, region: str):
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]

    # Replace NaN with None for JSON compatibility
    df = df.where(pd.notna(df), None)

    records = []
    for _, row in df.iterrows():
        # Extract year/month/week from WEEK column (datetime)
        week_date = None
        year_val = None
        month_val = None
        week_str = None

        if 'week' in row and row['week'] is not None:
            week_date = pd.to_datetime(row['week'])
            year_val = int(week_date.year)
            month_val = int(week_date.month)
            # Extract ISO week number (1-53)
            week_str = int(week_date.isocalendar().week)

        # Build metadata dict, excluding known columns
        # Convert to Python natives for JSON compatibility
        metadata_keys = {'country', 'admin1', 'admin2', 'year', 'month', 'week', 'events',
                        'fatalities', 'event_type', 'disorder_type', 'centroid_latitude', 'centroid_longitude'}
        metadata = {}
        for k, v in row.items():
            if k not in metadata_keys:
                # Convert pandas types to Python natives
                if pd.isna(v):
                    metadata[k] = None
                elif isinstance(v, (pd.Timestamp, datetime)):
                    metadata[k] = v.isoformat()
                elif isinstance(v, (int, float, str, bool)):
                    metadata[k] = v
                else:
                    metadata[k] = str(v)

        records.append((
            slug, region, row.get('country'), row.get('admin1'), row.get('admin2'),
            year_val,
            month_val,
            week_str,
            None, None,  # date_range_start, date_range_end
            float(row['centroid_latitude']) if row.get('centroid_latitude') is not None else None,
            float(row['centroid_longitude']) if row.get('centroid_longitude') is not None else None,
            int(row['events']) if row.get('events') is not None else None,
            int(row['fatalities']) if row.get('fatalities') is not None else None,
            row.get('event_type'), row.get('disorder_type'),
            Json(metadata),
            hash, datetime.now(timezone.utc)
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
    logger.info(f"Inserted {len(records)} rows → regional")

def collect_dataset(session: requests.Session, conn, dataset: Dict) -> bool:
    """Collect single dataset with full audit trail."""
    slug = dataset['slug']
    url = dataset['url']
    
    logger.info(f"\n{'='*70}\n{slug}\n{'='*70}")
    
    try:
        # Find link
        link_info = find_download_link(session, url)
        if not link_info:
            save_metadata(conn, dataset, 'failed', 'No download link found', None, None)
            return False
        
        # Download
        logger.info(f"Downloading via Strategy {link_info['strategy']}...")
        r = session.get(link_info['url'], stream=True, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        
        file_name = link_info['url'].split('/')[-1].split('?')[0]
        if not file_name.endswith(('.xlsx', '.csv')):
            cd = r.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                file_name = cd.split('filename=')[-1].strip('"\'')
            else:
                file_name = f"{slug}.xlsx"
        
        temp = Path(f"temp_{file_name}")
        with open(temp, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        
        file_size = temp.stat().st_size
        file_hash = calculate_hash(temp)
        logger.info(f"Downloaded {file_size:,} bytes, hash={file_hash[:12]}...")
        
        # Parse
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(temp)
        elif file_name.endswith('.csv'):
            df = pd.read_csv(temp)
        else:
            raise ValueError(f"Unsupported: {file_name}")
        
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Validate
        is_agg, reason = is_official_aggregate(df)
        if not is_agg:
            logger.error(f"INVALID: {reason}")
            save_metadata(conn, dataset, 'invalid', reason, r.status_code, link_info['strategy'],
                          {'download_url': link_info['url'], 'download_url_final': r.url, 'file_name': file_name,
                           'file_size': file_size, 'file_hash': file_hash, 'columns': list(df.columns),
                           'is_aggregated': False})
            temp.unlink()
            return False
        
        logger.info(f"✅ VALID: {reason}")
        
        # Detect
        agg_level, target = detect_granularity(df)
        logger.info(f"Granularity: {agg_level} → {target}")
        
        # Save RAW
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        raw_dir = RAW_DIR / slug / today
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / file_name
        temp.rename(raw_path)
        logger.info(f"Saved RAW: {raw_path}")
        
        # Metadata
        file_info = {
            'download_url': link_info['url'], 'download_url_final': r.url,
            'file_name': file_name, 'file_size': file_size, 'file_hash': file_hash,
            'aggregation_level': agg_level, 'columns': list(df.columns),
            'version_date': today, 'is_aggregated': True
        }
        save_metadata(conn, dataset, 'success', None, r.status_code, link_info['strategy'], file_info)
        
        # Insert
        if target == "acled_aggregated.country_year":
            insert_country_year(conn, df, slug, file_hash)
        elif target == "acled_aggregated.country_month_year":
            insert_country_month_year(conn, df, slug, file_hash)
        elif target == "acled_aggregated.regional":
            insert_regional(conn, df, slug, file_hash, dataset.get('region', 'Unknown'))
        
        logger.info(f"✅ SUCCESS: {slug}")
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: {slug} - {e}")
        save_metadata(conn, dataset, 'failed', str(e)[:500], None, None)
        return False

# ============================================================================
# Main
# ============================================================================

def main():
    logger.info("="*70)
    logger.info("ACLED Aggregated Data Collector v3.0")
    logger.info("="*70)
    logger.info(f"Datasets: {len(DATASETS)}")
    
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        session = create_session()
        conn = get_db()
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return
    
    results = {'success': 0, 'failed': 0, 'invalid': 0}
    
    for ds in DATASETS:
        success = collect_dataset(session, conn, ds)
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        time.sleep(POLITE_DELAY)
    
    conn.close()
    
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"✅ Success: {results['success']}")
    logger.info(f"❌ Failed/Invalid: {results['failed']}")
    logger.info(f"Debug: {DEBUG_DIR}")
    logger.info("="*70)

if __name__ == "__main__":
    main()
