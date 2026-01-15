#!/usr/bin/env python3
"""
ACLED Aggregated Data Collector - Production Grade
===================================================
Secure, resilient collector for ACLED official aggregated datasets.

SECURITY: All credentials via environment variables.
ROBUSTNESS: Multi-strategy link discovery with debug output.
VALIDATION: Ensures only official aggregates are ingested.

Author: Sofia Pulse Team
Version: 2.0 (Security & Robustness Hardened)
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

# ============================================================================
# Configuration from Environment Variables
# ============================================================================

# ACLED Credentials (REQUIRED via environment)
EMAIL = os.getenv("ACLED_EMAIL")
PASSWORD = os.getenv("ACLED_PASSWORD")

if not EMAIL or not PASSWORD:
    print("ERROR: ACLED_EMAIL and ACLED_PASSWORD environment variables required")
    print("Set them before running:")
    print("  export ACLED_EMAIL='your_email@example.com'")
    print("  export ACLED_PASSWORD='your_password'")
    sys.exit(1)

# PostgreSQL Configuration (with fallback defaults)
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

if not DB_CONFIG["password"]:
    print("ERROR: POSTGRES_PASSWORD environment variable required")
    sys.exit(1)

# Paths
BASE_DIR = Path("data/acled")
RAW_DIR = BASE_DIR / "raw"
DEBUG_DIR = BASE_DIR / "debug"

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
# Logging Setup (NO SENSITIVE DATA IN LOGS)
# ============================================================================

class SanitizingFilter(logging.Filter):
    """Remove sensitive data from logs."""
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password=***'),
        (r'SSESS[a-f0-9]+', 'SSESS***'),
        (r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', 'Bearer ***'),
    ]
    
    def filter(self, record):
        message = record.getMessage()
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        record.args = ()
        return True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('acled_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.addFilter(SanitizingFilter())

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


def is_official_aggregate(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that dataset is an OFFICIAL aggregate (not event-level).
    
    Returns: (is_aggregate, reason)
    """
    columns_lower = [col.lower() for col in df.columns]
    
    # EVENT-LEVEL INDICATORS (should NOT be present)
    event_indicators = [
        'event_date', 'event_id', 'data_id',
        'actor1', 'actor2', 'assoc_actor_1', 'assoc_actor_2',
        'inter1', 'inter2',
        'latitude', 'longitude',  # Event location (not centroid)
        'geo_precision', 'time_precision',
        'source', 'source_scale', 'notes'
    ]
    
    found_event_indicators = [i for i in event_indicators if i in columns_lower]
    if found_event_indicators:
        return False, f"Event-level columns detected: {found_event_indicators}"
    
    # AGGREGATE INDICATORS (should be present)
    has_events = 'events' in columns_lower or 'fatalities' in columns_lower
    has_temporal = any(t in columns_lower for t in ['year', 'month', 'week'])
    has_geo = any(g in columns_lower for g in ['country', 'admin1', 'region'])
    
    if not has_events:
        return False, "Missing 'events' or 'fatalities' count column"
    
    if not has_temporal:
        return False, "Missing temporal aggregation column (year/month/week)"
    
    # Passed all checks
    return True, "Valid official aggregate"


def detect_aggregation_type(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Detect aggregation granularity.
    Returns: (aggregation_level, target_table)
    """
    columns_lower = [col.lower() for col in df.columns]
    
    if 'year' in columns_lower and 'month' in columns_lower:
        return ("country-month-year", "acled_aggregated.country_month_year")
    elif 'year' in columns_lower and 'country' in columns_lower:
        return ("country-year", "acled_aggregated.country_year")
    elif 'week' in columns_lower or 'admin1' in columns_lower:
        return ("regional", "acled_aggregated.regional")
    else:
        return ("country-year", "acled_aggregated.country_year")  # default


def save_debug_html(slug: str, html_content: str, status_code: int, final_url: str):
    """Save HTML for debugging failed scrapes (NO SENSITIVE DATA)."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H%M%S')
    debug_file = DEBUG_DIR / f"{slug}-{timestamp}.html"
    
    # Sanitize HTML before saving (remove any tokens/cookies in HTML)
    sanitized = re.sub(r'SSESS[a-f0-9]+', 'SSESS***', html_content)
    
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(f"<!-- Status: {status_code} -->\n")
        f.write(f"<!-- Final URL: {final_url} -->\n")
        f.write(f"<!-- Timestamp: {timestamp} UTC -->\n\n")
        f.write(sanitized)
    
    logger.info(f"Debug HTML saved: {debug_file}")


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
    
    # Verify session (check for Drupal session cookie)
    cookie_names = list(session.cookies.keys())
    has_session = any(name.startswith('SSESS') for name in cookie_names)
    
    if has_session:
        logger.info("Authentication successful")
        return session
    else:
        raise Exception("Authentication failed - no session cookie")


def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def find_download_link(session: requests.Session, page_url: str) -> Optional[Dict]:
    """
    Multi-strategy download link discovery.
    
    Returns: {
        'url': str,
        'strategy': str,
        'final_url': str,
        'content_type': str
    }
    """
    try:
        r = session.get(page_url, timeout=TIMEOUT, allow_redirects=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        final_url = r.url
        
        # STRATEGY A: Direct <a href> with file extensions
        logger.info("Strategy A: Looking for direct file links...")
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(ext in href.lower() for ext in ['.xlsx', '.csv', '.zip']):
                if not href.startswith('http'):
                    href = 'https://acleddata.com' + href
                logger.info(f"Found via Strategy A: {href}")
                return {
                    'url': href,
                    'strategy': 'direct_link',
                    'final_url': href,
                    'content_type': 'unknown'
                }
        
        # STRATEGY B: Links/buttons with "Download" text
        logger.info("Strategy B: Looking for 'Download' buttons/links...")
        for elem in soup.find_all(['a', 'button']):
            text = elem.get_text().lower()
            if 'download' in text or 'export' in text:
                href = elem.get('href') or elem.get('data-href')
                if href:
                    if not href.startswith('http'):
                        href = 'https://acleddata.com' + href
                    logger.info(f"Found via Strategy B: {href}")
                    return {
                        'url': href,
                        'strategy': 'download_button',
                        'final_url': href,
                        'content_type': 'unknown'
                    }
        
        # STRATEGY C: Check all links and follow redirects to check Content-Type
        logger.info("Strategy C: Checking Content-Type of all links...")
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') or href.startswith('/'):
                if not href.startswith('http'):
                    href = 'https://acleddata.com' + href
                
                # Quick HEAD request to check content type
                try:
                    head_r = session.head(href, timeout=5, allow_redirects=True)
                    content_type = head_r.headers.get('Content-Type', '').lower()
                    
                    if any(ct in content_type for ct in ['xlsx', 'csv', 'spreadsheet', 'octet-stream']):
                        logger.info(f"Found via Strategy C: {href} (Content-Type: {content_type})")
                        return {
                            'url': href,
                            'strategy': 'content_type_check',
                            'final_url': head_r.url,
                            'content_type': content_type
                        }
                except:
                    continue
        
        logger.warning("No download link found with any strategy")
        return None
        
    except Exception as e:
        logger.error(f"Error in link discovery: {e}")
        return None


def check_if_already_collected(conn, slug: str, file_hash: str) -> bool:
    """Check if this exact version was already collected."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM acled_metadata.datasets
            WHERE dataset_slug = %s AND file_hash = %s
        """, (slug, file_hash))
        return cur.fetchone() is not None


def save_metadata(conn, dataset: Dict, file_info: Dict, is_aggregate: bool, validation_reason: str):
    """Save or update metadata in PostgreSQL."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO acled_metadata.datasets (
                dataset_slug, source_url, download_url, aggregation_level, region,
                file_hash, file_name, file_size_bytes, collected_at, is_aggregated,
                source_type, detected_columns, version_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dataset_slug, file_hash) DO UPDATE SET
                collected_at = EXCLUDED.collected_at,
                updated_at = NOW()
        """, (
            dataset['slug'],
            dataset['url'],
            file_info.get('download_url_final'),
            file_info.get('aggregation_level'),
            dataset.get('region'),
            file_info['file_hash'],
            file_info['file_name'],
            file_info['file_size'],
            datetime.now(timezone.utc),
            is_aggregate,
            'ACLED_OFFICIAL_AGGREGATE' if is_aggregate else 'ACLED_UNVALIDATED',
            Json(file_info.get('columns', [])),
            file_info.get('version_date')
        ))
    conn.commit()
    logger.info(f"Metadata saved (is_aggregated={is_aggregate}, reason={validation_reason})")


def insert_to_country_year(conn, df: pd.DataFrame, dataset_slug: str, file_hash: str):
    """Insert data into country_year table."""
    df_clean = df.copy()
    df_clean.columns = [to_snake_case(col) for col in df_clean.columns]
    
    records = []
    for _, row in df_clean.iterrows():
        record = (
            dataset_slug,
            row.get('country', ''),
            int(row.get('year', 0)) if pd.notna(row.get('year')) else None,
            int(row.get('events', 0)) if pd.notna(row.get('events')) else None,
            int(row.get('fatalities')) if 'fatalities' in row and pd.notna(row.get('fatalities')) else None,
            Json({k: v for k, v in row.items() if k not in ['country', 'year', 'events', 'fatalities']}),
            file_hash,
            datetime.now(timezone.utc)
        )
        records.append(record)
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO acled_aggregated.country_year (
                dataset_slug, country, year, events, fatalities, metadata, source_file_hash, collected_at
            ) VALUES %s
            ON CONFLICT (dataset_slug, country, year, source_file_hash) DO NOTHING
        """, records)
    
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
            None,
            None,
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
    """Collect a single dataset with full validation and error handling."""
    slug = dataset['slug']
    url = dataset['url']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing: {slug}")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*70}")
    
    try:
        # Multi-strategy link discovery
        link_info = find_download_link(session, url)
        
        if not link_info:
            logger.error(f"No download link found")
            # Save debug HTML
            r = session.get(url, timeout=TIMEOUT)
            save_debug_html(slug, r.text, r.status_code, r.url)
            return False
        
        download_url = link_info['url']
        logger.info(f"Download strategy: {link_info['strategy']}")
        logger.info(f"Downloading from: {download_url}")
        
        # Download file
        response = session.get(download_url, stream=True, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        file_name = download_url.split('/')[-1].split('?')[0]
        if not file_name.endswith(('.xlsx', '.csv')):
            # Try to get from Content-Disposition header
            content_disp = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disp:
                file_name = content_disp.split('filename=')[-1].strip('"\'')
            else:
                file_name = f"{slug}.xlsx"  # fallback
        
        temp_file = Path(f"temp_{file_name}")
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = temp_file.stat().st_size
        file_hash = calculate_file_hash(temp_file)
        logger.info(f"Downloaded {file_size:,} bytes, hash: {file_hash[:16]}...")
        
        # Check if already collected
        if check_if_already_collected(conn, slug, file_hash):
            logger.info(f"Already collected (hash match). Skipping.")
            temp_file.unlink()
            return True
        
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
        logger.info(f"Columns: {list(df.columns)[:5]}...")  # Only first 5 for brevity
        
        # VALIDATE: Ensure it's an official aggregate
        is_aggregate, reason = is_official_aggregate(df)
        if not is_aggregate:
            logger.error(f"VALIDATION FAILED: {reason}")
            logger.error(f"This dataset will NOT be inserted into acled_aggregated")
            
            # Save metadata but mark as NOT aggregated
            file_info = {
                'download_url_final': response.url,
                'file_name': file_name,
                'file_size': file_size,
                'file_hash': file_hash,
                'aggregation_level': 'INVALID',
                'columns': list(df.columns),
                'version_date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
            }
            save_metadata(conn, dataset, file_info, False, reason)
            temp_file.unlink()
            return False
        
        logger.info(f"VALIDATION PASSED: {reason}")
        
        # Detect aggregation type
        agg_level, target_table = detect_aggregation_type(df)
        logger.info(f"Detected: {agg_level} → {target_table}")
        
        # Save metadata
        file_info = {
            'download_url_final': response.url,
            'file_name': file_name,
            'file_size': file_size,
            'file_hash': file_hash,
            'aggregation_level': agg_level,
            'columns': list(df.columns),
            'version_date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
        }
        save_metadata(conn, dataset, file_info, True, reason)
        
        # Insert into appropriate table
        if target_table == "acled_aggregated.country_year":
            insert_to_country_year(conn, df, slug, file_hash)
        elif target_table == "acled_aggregated.country_month_year":
            insert_to_country_month_year(conn, df, slug, file_hash)
        elif target_table == "acled_aggregated.regional":
            insert_to_regional(conn, df, slug, file_hash, dataset.get('region', 'Unknown'))
        
        temp_file.unlink()
        
        logger.info(f"✅ Successfully collected: {slug}")
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
    logger.info("ACLED Aggregated Data Collector v2.0")
    logger.info("="*70)
    logger.info(f"Datasets: {len(DATASETS)}")
    logger.info(f"Target: PostgreSQL {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    
    # Create directories
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    
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
    results = {'success': 0, 'failed': 0, 'invalid': 0}
    
    for dataset in DATASETS:
        success = collect_dataset(session, conn, dataset)
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        time.sleep(2)  # Polite delay
    
    conn.close()
    
    logger.info("\n" + "="*70)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*70)
    logger.info(f"✅ Success: {results['success']}")
    logger.info(f"❌ Failed: {results['failed']}")
    logger.info(f"Total: {len(DATASETS)}")
    logger.info("="*70)
    logger.info(f"Debug files: {DEBUG_DIR}")


if __name__ == "__main__":
    main()
