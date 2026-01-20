#!/usr/bin/env python3
"""
Fast ACLED Regional Loader - Uses COPY for 100x speedup
Loads directly from downloaded Excel files into acled_aggregated.regional
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from pathlib import Path
from io import StringIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fast_loader')

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '91.98.158.19'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'dbs_sofia'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DB', 'sofia')
}

# Regional files to load
REGIONAL_FILES = [
    {'slug': 'aggregated-europe-central-asia', 'region': 'Europe and Central Asia',
     'file': 'data/acled/raw/aggregated-europe-central-asia/2026-01-15/Europe-Central-Asia_aggregated_data_up_to-2026-01-03.xlsx'},
    {'slug': 'aggregated-us-canada', 'region': 'United States and Canada',
     'file': 'data/acled/raw/aggregated-us-canada/2026-01-15/US-and-Canada_aggregated_data_up_to-2026-01-03.xlsx'},
    {'slug': 'aggregated-latin-america-caribbean', 'region': 'Latin America and Caribbean',
     'file': 'data/acled/raw/aggregated-latin-america-caribbean/2026-01-15/Latin-America-the-Caribbean_aggregated_data_up_to-2026-01-03.xlsx'},
    {'slug': 'aggregated-middle-east', 'region': 'Middle East',
     'file': 'data/acled/raw/aggregated-middle-east/2026-01-15/Middle-East_aggregated_data_up_to-2026-01-03.xlsx'},
    {'slug': 'aggregated-asia-pacific', 'region': 'Asia Pacific',
     'file': 'data/acled/raw/aggregated-asia-pacific/2026-01-15/Asia-Pacific_aggregated_data_up_to-2026-01-03.xlsx'},
    {'slug': 'aggregated-africa', 'region': 'Africa',
     'file': 'data/acled/raw/aggregated-africa/2026-01-15/Africa_aggregated_data_up_to-2026-01-03.xlsx'}
]


def load_regional_file(conn, file_info):
    """Load one regional file using COPY (fast!)"""
    slug = file_info['slug']
    region = file_info['region']
    file_path = file_info['file']

    if not Path(file_path).exists():
        logger.warning(f"File not found: {file_path}")
        return 0

    logger.info(f"Loading {slug}...")

    # Read Excel
    df = pd.read_excel(file_path)
    logger.info(f"  Read {len(df):,} rows")

    # Normalize column names
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]

    # Extract year/month/week from WEEK column
    df['week_date'] = pd.to_datetime(df['week'])
    df['year_val'] = df['week_date'].dt.year
    df['month_val'] = df['week_date'].dt.month
    df['week_num'] = df['week_date'].dt.isocalendar().week

    # Build final dataframe for COPY
    copy_df = pd.DataFrame({
        'dataset_slug': slug,
        'region': region,
        'country': df.get('country', None),
        'admin1': df.get('admin1', None),
        'admin2': None,  # Not in regional files
        'year': df['year_val'],
        'month': df['month_val'],
        'week': df['week_num'],
        'date_range_start': None,
        'date_range_end': None,
        'centroid_latitude': df.get('centroid_latitude', None),
        'centroid_longitude': df.get('centroid_longitude', None),
        'events': df.get('events', None),
        'fatalities': df.get('fatalities', None),
        'event_type': df.get('event_type', None),
        'disorder_type': df.get('disorder_type', None),
        'metadata': None,  # Skip metadata for speed
        'source_file_hash': 'fast_load',
        'collected_at': pd.Timestamp.now()
    })

    # Convert NaN to None
    copy_df = copy_df.where(pd.notna(copy_df), None)

    # Use COPY for ultra-fast insert
    buffer = StringIO()
    copy_df.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
    buffer.seek(0)

    cursor = conn.cursor()
    try:
        cursor.copy_from(
            buffer,
            'acled_aggregated.regional',
            columns=['dataset_slug', 'region', 'country', 'admin1', 'admin2',
                    'year', 'month', 'week', 'date_range_start', 'date_range_end',
                    'centroid_latitude', 'centroid_longitude', 'events', 'fatalities',
                    'event_type', 'disorder_type', 'metadata', 'source_file_hash', 'collected_at'],
            null='\\N'
        )
        conn.commit()
        logger.info(f"  ✅ Inserted {len(df):,} rows")
        return len(df)
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    logger.info("=" * 60)
    logger.info("Fast ACLED Regional Loader")
    logger.info("=" * 60)

    total_inserted = 0

    for file_info in REGIONAL_FILES:
        inserted = load_regional_file(conn, file_info)
        total_inserted += inserted

    conn.close()

    logger.info("=" * 60)
    logger.info(f"✅ Total inserted: {total_inserted:,} rows")
    logger.info("=" * 60)

    # Verify
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), COUNT(DISTINCT country)
        FROM acled_aggregated.regional
    """)
    total, countries = cursor.fetchone()
    logger.info(f"\n📊 Regional table: {total:,} records from {countries} countries")
    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
