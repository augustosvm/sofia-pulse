#!/usr/bin/env python3
"""
ACLED Aggregated Data Collector
================================
Resilient scraper for ACLED public aggregated datasets.
Downloads, versions, and normalizes all official aggregated files.

Author: Sofia Pulse Team
Date: 2026-01-15
"""

import requests
from bs4 import BeautifulSoup
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import time
import logging
from typing import Dict, Optional, List
import sys

# ============================================================================
# Configuration
# ============================================================================

# Login credentials (required for file access)
EMAIL = "augusto@tiespecialistas.com.br"
PASSWORD = "75August!@"

# Base paths
BASE_DIR = Path("data/acled")
RAW_DIR = BASE_DIR / "raw"
METADATA_DIR = BASE_DIR / "metadata"

# Request configuration
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds

# Dataset definitions
DATASETS = [
    {
        "slug": "political-violence-country-year",
        "url": "https://acleddata.com/aggregated/number-political-violence-events-country-year",
        "aggregation_level": "country-year",
        "region": "Global"
    },
    {
        "slug": "political-violence-country-month-year",
        "url": "https://acleddata.com/aggregated/number-political-violence-events-country-month-year",
        "aggregation_level": "country-month-year",
        "region": "Global"
    },
    {
        "slug": "demonstrations-country-year",
        "url": "https://acleddata.com/aggregated/number-demonstration-events-country-year",
        "aggregation_level": "country-year",
        "region": "Global"
    },
    {
        "slug": "civilian-targeting-country-year",
        "url": "https://acleddata.com/aggregated/number-events-targeting-civilians-country-year",
        "aggregation_level": "country-year",
        "region": "Global"
    },
    {
        "slug": "fatalities-country-year",
        "url": "https://acleddata.com/aggregated/number-reported-fatalities-country-year",
        "aggregation_level": "country-year",
        "region": "Global"
    },
    {
        "slug": "civilian-fatalities-country-year",
        "url": "https://acleddata.com/aggregated/number-reported-civilian-fatalities-direct-targeting-country-year",
        "aggregation_level": "country-year",
        "region": "Global"
    },
    {
        "slug": "aggregated-europe-central-asia",
        "url": "https://acleddata.com/aggregated/aggregated-data-europe-and-central-asia",
        "aggregation_level": "regional",
        "region": "Europe and Central Asia"
    },
    {
        "slug": "aggregated-us-canada",
        "url": "https://acleddata.com/aggregated/aggregated-data-united-states-canada",
        "aggregation_level": "regional",
        "region": "United States and Canada"
    },
    {
        "slug": "aggregated-latin-america-caribbean",
        "url": "https://acleddata.com/aggregated/aggregated-data-latin-america-caribbean",
        "aggregation_level": "regional",
        "region": "Latin America and Caribbean"
    },
    {
        "slug": "aggregated-middle-east",
        "url": "https://acleddata.com/aggregated/aggregated-data-middle-east",
        "aggregation_level": "regional",
        "region": "Middle East"
    },
    {
        "slug": "aggregated-asia-pacific",
        "url": "https://acleddata.com/aggregated/aggregated-data-asia-pacific",
        "aggregation_level": "regional",
        "region": "Asia Pacific"
    },
    {
        "slug": "aggregated-africa",
        "url": "https://acleddata.com/aggregated/aggregated-data-africa",
        "aggregation_level": "regional",
        "region": "Africa"
    }
]

# ============================================================================
# Setup Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('acled_collector.log'),
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


def load_metadata(slug: str) -> Optional[Dict]:
    """Load existing metadata for a dataset."""
    metadata_file = METADATA_DIR / f"{slug}.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return None


def save_metadata(slug: str, metadata: Dict):
    """Save metadata for a dataset."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_file = METADATA_DIR / f"{slug}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {metadata_file}")


def create_session() -> requests.Session:
    """Create and authenticate a session with ACLED."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://acleddata.com"
    })
    
    logger.info("Authenticating with ACLED...")
    
    # Get login page
    r = session.get("https://acleddata.com/user/login", timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Find login form
    form = soup.find('form', {'id': 'user-login-form'})
    if not form:
        raise Exception("Login form not found")
    
    # Extract form data
    action = form.get('action')
    if not action.startswith('http'):
        action = "https://acleddata.com" + action
    
    payload = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        value = inp.get('value', '')
        if name:
            payload[name] = value
    
    # Add credentials
    payload['name'] = EMAIL
    payload['pass'] = PASSWORD
    if 'op' not in payload:
        payload['op'] = 'Log in'
    
    # Submit login
    r_login = session.post(action, data=payload, timeout=TIMEOUT)
    
    # Verify login - check for Drupal session cookie (starts with SSESS)
    cookie_names = list(session.cookies.keys())
    has_session = any(name.startswith('SSESS') for name in cookie_names)
    
    if has_session:
        logger.info("✅ Authentication successful")
        logger.debug(f"Session cookies: {cookie_names}")
        return session
    else:
        logger.error(f"Authentication failed. Cookies: {cookie_names}")
        raise Exception("Authentication failed - no session cookie found")


def download_with_retry(session: requests.Session, url: str, max_retries: int = MAX_RETRIES) -> requests.Response:
    """Download a file with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = session.get(url, stream=True, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = RETRY_BACKOFF ** attempt
                logger.warning(f"Download failed (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Download failed after {max_retries} attempts")
                raise


def find_download_link(session: requests.Session, page_url: str) -> Optional[str]:
    """Find the download link on an ACLED aggregated data page."""
    try:
        r = session.get(page_url, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for links to XLSX or CSV files
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(ext in href.lower() for ext in ['.xlsx', '.csv', '.zip']):
                # Make absolute URL
                if not href.startswith('http'):
                    href = 'https://acleddata.com' + href
                logger.info(f"Found download link: {href}")
                return href
        
        logger.warning(f"No download link found on {page_url}")
        return None
    
    except Exception as e:
        logger.error(f"Error finding download link: {e}")
        return None


def collect_dataset(session: requests.Session, dataset: Dict) -> bool:
    """
    Collect a single dataset.
    Returns True if successful, False otherwise.
    """
    slug = dataset['slug']
    url = dataset['url']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing dataset: {slug}")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*70}")
    
    try:
        # Find download link
        download_url = find_download_link(session, url)
        if not download_url:
            logger.error(f"Skipping {slug}: no download link found")
            return False
        
        # Extract filename from URL
        file_name = download_url.split('/')[-1].split('?')[0]
        
        # Download file to temporary location
        logger.info(f"Downloading {file_name}...")
        response = download_with_retry(session, download_url)
        
        # Save to temporary file first
        temp_file = Path(f"temp_{file_name}")
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded {temp_file.stat().st_size} bytes")
        
        # Calculate hash
        file_hash = calculate_file_hash(temp_file)
        logger.info(f"File hash: {file_hash[:16]}...")
        
        # Check if we already have this version
        existing_metadata = load_metadata(slug)
        if existing_metadata and existing_metadata.get('file_hash') == file_hash:
            logger.info(f"✅ File unchanged (hash match). Skipping save.")
            temp_file.unlink()
            return True
        
        # Create versioned directory
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        dataset_dir = RAW_DIR / slug / today
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file to final location
        final_path = dataset_dir / file_name
        temp_file.rename(final_path)
        logger.info(f"Saved to: {final_path}")
        
        # Create metadata
        metadata = {
            "dataset_slug": slug,
            "source_url": url,
            "download_url": download_url,
            "file_name": file_name,
            "file_path": str(final_path),
            "file_hash": file_hash,
            "file_size_bytes": final_path.stat().st_size,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "region": dataset.get('region'),
            "aggregation_level": dataset.get('aggregation_level'),
            "version_date": today
        }
        
        save_metadata(slug, metadata)
        
        logger.info(f"✅ Successfully collected: {slug}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to collect {slug}: {e}")
        return False


# ============================================================================
# Main Collection Pipeline
# ============================================================================

def main():
    """Main collection pipeline."""
    logger.info("="*70)
    logger.info("ACLED Aggregated Data Collector")
    logger.info("="*70)
    logger.info(f"Total datasets to collect: {len(DATASETS)}")
    logger.info(f"Output directory: {BASE_DIR.resolve()}")
    
    # Create directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create authenticated session
    try:
        session = create_session()
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")
        return
    
    # Collect each dataset
    results = {
        'success': 0,
        'failed': 0,
        'skipped': 0
    }
    
    for dataset in DATASETS:
        success = collect_dataset(session, dataset)
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        
        # Polite delay between requests
        time.sleep(2)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*70)
    logger.info(f"✅ Successful: {results['success']}")
    logger.info(f"❌ Failed: {results['failed']}")
    logger.info(f"Total: {len(DATASETS)}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
