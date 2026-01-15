#!/usr/bin/env python3
"""
GDELT Events Collector - Security Layer
Collects geolocated events from GDELT Events 2.0 Database
Uses BigQuery public dataset or CSV exports for proper lat/lon data
"""

import os
import sys
import json
import hashlib
import logging
import requests
import zipfile
import csv
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gdelt_events_collector')

# Database config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', '91.98.158.19')),
    'port': os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'SofiaPulse2025Secure@DB')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia_db'))
}

# GDELT 2.0 Events export URL pattern
# Format: http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.zip
GDELT_EXPORT_BASE = "http://data.gdeltproject.org/gdeltv2"
GDELT_LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# CAMEO event codes for filtering relevant events
RELEVANT_CAMEO_ROOTS = {
    '14': 'Protest',
    '15': 'Force',
    '17': 'Coerce',
    '18': 'Assault',
    '19': 'Fight',
    '20': 'Mass Violence'
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_country_mapping(conn) -> Dict[str, int]:
    """Load country code -> id mapping"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, iso_alpha2 FROM sofia.countries WHERE iso_alpha2 IS NOT NULL")
    mapping = {row[1]: row[0] for row in cursor.fetchall()}
    cursor.close()
    return mapping


def fetch_latest_gdelt_url() -> Optional[str]:
    """Get the latest GDELT export file URL"""
    try:
        response = requests.get(GDELT_LASTUPDATE, timeout=30)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                if '.export.CSV.zip' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
        return None
    except Exception as e:
        logger.error(f"Error fetching GDELT last update: {e}")
        return None


def fetch_gdelt_events(hours_back: int = 24) -> List[Dict]:
    """Fetch GDELT events from the last N hours"""
    events = []

    # Get list of export files to fetch
    now = datetime.utcnow()
    urls_to_fetch = []

    # GDELT updates every 15 minutes, so for 24 hours we need ~96 files
    # Let's be practical and fetch every hour (24 files max)
    for h in range(min(hours_back, 24)):
        dt = now - timedelta(hours=h)
        # Round to nearest 15-minute interval
        minute = (dt.minute // 15) * 15
        timestamp = dt.strftime(f"%Y%m%d%H{minute:02d}00")
        url = f"{GDELT_EXPORT_BASE}/{timestamp}.export.CSV.zip"
        urls_to_fetch.append(url)

    # Also try the latest
    latest_url = fetch_latest_gdelt_url()
    if latest_url and latest_url not in urls_to_fetch:
        urls_to_fetch.insert(0, latest_url)

    logger.info(f"Fetching {len(urls_to_fetch)} GDELT export files...")

    for url in urls_to_fetch[:12]:  # Limit to 12 files (3 hours) to avoid timeout
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                events.extend(parse_gdelt_export(response.content))
                logger.info(f"Parsed {url.split('/')[-1]}")
            else:
                logger.debug(f"File not found: {url}")
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")

    return events


def parse_gdelt_export(zip_content: bytes) -> List[Dict]:
    """Parse GDELT export CSV from zip file"""
    events = []

    try:
        with zipfile.ZipFile(BytesIO(zip_content)) as zf:
            for filename in zf.namelist():
                if filename.endswith('.CSV'):
                    with zf.open(filename) as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        reader = csv.reader(StringIO(content), delimiter='\t')

                        for row in reader:
                            if len(row) < 58:
                                continue

                            try:
                                # GDELT 2.0 column indices
                                global_event_id = row[0]
                                event_date = row[1]  # YYYYMMDD
                                event_code = row[26]  # CAMEO event code
                                event_root_code = row[28]
                                goldstein = row[30]
                                num_mentions = row[31]
                                num_sources = row[32]
                                num_articles = row[33]
                                avg_tone = row[34]

                                # Actor geo
                                actor1_geo_type = row[35]
                                actor1_geo_fullname = row[36]
                                actor1_geo_country = row[37]
                                actor1_geo_lat = row[39]
                                actor1_geo_lon = row[40]

                                # Action geo (primary location)
                                action_geo_type = row[50]
                                action_geo_fullname = row[51]
                                action_geo_country = row[52]
                                action_geo_adm1 = row[53]
                                action_geo_lat = row[55]
                                action_geo_lon = row[56]

                                source_url = row[57] if len(row) > 57 else None

                                # Filter: only events with geo and relevant types
                                if not action_geo_lat or not action_geo_lon:
                                    continue

                                try:
                                    lat = float(action_geo_lat)
                                    lon = float(action_geo_lon)
                                    if lat == 0 and lon == 0:
                                        continue
                                except:
                                    continue

                                # Filter by CAMEO root code (optional - can remove for more data)
                                # if event_root_code not in RELEVANT_CAMEO_ROOTS:
                                #     continue

                                # Parse date
                                try:
                                    parsed_date = datetime.strptime(event_date[:8], '%Y%m%d').date()
                                except:
                                    parsed_date = datetime.utcnow().date()

                                # Calculate severity score
                                try:
                                    goldstein_val = float(goldstein) if goldstein else 0
                                    tone_val = float(avg_tone) if avg_tone else 0
                                    mentions = int(num_mentions) if num_mentions else 1
                                    # Severity: negative goldstein = conflict, amplified by mentions
                                    severity = max(1, abs(min(0, goldstein_val)) * (1 + mentions / 10))
                                except:
                                    severity = 1.0

                                event = {
                                    'source_id': global_event_id,
                                    'event_date': parsed_date,
                                    'country_code': action_geo_country[:2] if action_geo_country else None,
                                    'admin1': action_geo_adm1,
                                    'latitude': lat,
                                    'longitude': lon,
                                    'event_type': RELEVANT_CAMEO_ROOTS.get(event_root_code, f'CAMEO_{event_root_code}'),
                                    'sub_event_type': event_code,
                                    'severity_score': severity,
                                    'source_url': source_url,
                                    'raw_payload': {
                                        'global_event_id': global_event_id,
                                        'event_code': event_code,
                                        'goldstein': goldstein,
                                        'avg_tone': avg_tone,
                                        'num_mentions': num_mentions,
                                        'action_geo_fullname': action_geo_fullname
                                    }
                                }
                                events.append(event)

                            except Exception as e:
                                continue

    except Exception as e:
        logger.error(f"Error parsing GDELT zip: {e}")

    return events


def save_to_security_events(events: List[Dict], country_mapping: Dict[str, int]) -> int:
    """Save events to security_events table"""
    if not events:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = 0

    for event in events:
        try:
            country_id = country_mapping.get(event['country_code'])

            cursor.execute("""
                INSERT INTO sofia.security_events
                (source, source_id, event_date, country_code, country_id, admin1,
                 latitude, longitude, event_type, sub_event_type, severity_score,
                 source_url, raw_payload)
                VALUES ('GDELT', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, source_id) DO UPDATE SET
                    event_date = EXCLUDED.event_date,
                    severity_score = EXCLUDED.severity_score,
                    raw_payload = EXCLUDED.raw_payload,
                    ingested_at = now()
            """, (
                event['source_id'],
                event['event_date'],
                event['country_code'],
                country_id,
                event.get('admin1'),
                event['latitude'],
                event['longitude'],
                event.get('event_type'),
                event.get('sub_event_type'),
                event['severity_score'],
                event.get('source_url'),
                json.dumps(event['raw_payload'])
            ))
            inserted += 1

        except Exception as e:
            logger.warning(f"Error inserting event {event.get('source_id')}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()

    return inserted


def main():
    logger.info("=" * 60)
    logger.info("GDELT Events Collector - Security Layer")
    logger.info("=" * 60)

    conn = get_db_connection()
    country_mapping = get_country_mapping(conn)
    conn.close()
    logger.info(f"Loaded {len(country_mapping)} country mappings")

    # Fetch events
    events = fetch_gdelt_events(hours_back=6)
    logger.info(f"Fetched {len(events)} geolocated events")

    if not events:
        logger.warning("No events collected")
        return

    # Save to database
    inserted = save_to_security_events(events, country_mapping)
    logger.info(f"Inserted/updated {inserted} events in security_events")

    # Summary
    countries = {}
    for e in events:
        c = e.get('country_code', 'XX')
        countries[c] = countries.get(c, 0) + 1

    logger.info("\nTop countries:")
    for c, count in sorted(countries.items(), key=lambda x: -x[1])[:10]:
        logger.info(f"  {c}: {count}")

    logger.info("=" * 60)
    logger.info("GDELT collection complete")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
