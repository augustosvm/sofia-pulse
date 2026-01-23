#!/usr/bin/env python3
"""
Sofia Pulse - GA4 BigQuery Collector (Production-Grade)

Collects Google Analytics 4 events from BigQuery export and stores in Postgres.

Features:
- Incremental collection by date range
- Idempotent (deduplication via event_hash)
- Auto-detects GA4 dataset
- Batch inserts with execute_values
- Production-grade logging
"""

import os
import sys
import argparse
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import execute_values
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIG
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'tiespecialistas-tts')
GA4_BQ_DATASET = os.getenv('GA4_BQ_DATASET')  # Optional override

BATCH_SIZE = 1000  # Rows per insert batch

# ============================================================================
# UTILITIES
# ============================================================================

def normalize_url_to_path(url):
    """
    Extract path from full URL.

    Example: https://example.com/page?foo=bar#section -> /page
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        path = parsed.path or '/'

        # Ensure starts with /
        if not path.startswith('/'):
            path = '/' + path

        return path

    except Exception:
        return None

def generate_event_hash(event):
    """
    Generate deterministic SHA256 hash for deduplication.

    Hash components:
    - event_date
    - event_timestamp
    - event_name
    - user_pseudo_id
    - page_location
    - ga_session_id
    """
    components = [
        str(event.get('event_date') or ''),
        str(event.get('event_timestamp') or ''),
        str(event.get('event_name') or ''),
        str(event.get('user_pseudo_id') or ''),
        str(event.get('page_location') or ''),
        str(event.get('ga_session_id') or ''),
    ]

    hash_input = '|'.join(components).encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()

def detect_ga4_dataset(client, project_id):
    """
    Auto-detect GA4 dataset (analytics_*).

    Returns: dataset_id or None
    """
    try:
        datasets = list(client.list_datasets(project_id))

        for dataset in datasets:
            if dataset.dataset_id.startswith('analytics_'):
                return dataset.dataset_id

        return None

    except Exception as e:
        print(f"[ERROR] Failed to detect GA4 dataset: {e}")
        return None

# ============================================================================
# BIGQUERY FUNCTIONS
# ============================================================================

def build_date_range(start_date, end_date):
    """
    Build list of date strings (YYYYMMDD) for table suffix.

    Args:
        start_date: datetime.date
        end_date: datetime.date

    Returns: list of strings ['20260101', '20260102', ...]
    """
    date_range = []
    current = start_date

    while current <= end_date:
        date_range.append(current.strftime('%Y%m%d'))
        current += timedelta(days=1)

    return date_range

def fetch_events_from_bigquery(client, project_id, dataset_id, start_date, end_date, include_intraday=False):
    """
    Fetch GA4 events from BigQuery for date range.

    Args:
        client: bigquery.Client
        project_id: str
        dataset_id: str
        start_date: datetime.date
        end_date: datetime.date
        include_intraday: bool

    Returns: list of dicts
    """
    # Build table suffix list
    date_suffixes = build_date_range(start_date, end_date)

    if not date_suffixes:
        print("[WARNING] No dates to fetch")
        return []

    # Build table wildcard
    # Use _TABLE_SUFFIX for date filtering
    table_pattern = f"`{project_id}.{dataset_id}.events_*`"

    # Build WHERE clause for table suffix
    start_suffix = date_suffixes[0]
    end_suffix = date_suffixes[-1]

    query = f"""
    SELECT
        event_date,
        event_timestamp,
        event_name,
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') as ga_session_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') as page_location,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title') as page_title,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') as engagement_time_ms,
        traffic_source.source as source,
        traffic_source.medium as medium,
        device.category as device_category,
        geo.country as country
    FROM {table_pattern}
    WHERE _TABLE_SUFFIX BETWEEN '{start_suffix}' AND '{end_suffix}'
        AND event_name IS NOT NULL
    """

    # If include_intraday, also query intraday tables
    # Note: This doubles the query, so keep it optional
    if include_intraday:
        intraday_pattern = f"`{project_id}.{dataset_id}.events_intraday_*`"
        query += f"""
        UNION ALL
        SELECT
            event_date,
            event_timestamp,
            event_name,
            user_pseudo_id,
            (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') as ga_session_id,
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') as page_location,
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title') as page_title,
            (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') as engagement_time_ms,
            traffic_source.source as source,
            traffic_source.medium as medium,
            device.category as device_category,
            geo.country as country
        FROM {intraday_pattern}
        WHERE _TABLE_SUFFIX BETWEEN '{start_suffix}' AND '{end_suffix}'
            AND event_name IS NOT NULL
        """

    print(f"[INFO] Fetching events from {start_suffix} to {end_suffix}...")

    try:
        query_job = client.query(query)
        results = query_job.result()

        events = []

        for row in results:
            event = {
                'event_date': row.event_date,
                'event_timestamp': row.event_timestamp,
                'event_name': row.event_name,
                'user_pseudo_id': row.user_pseudo_id,
                'ga_session_id': row.ga_session_id,
                'page_location': row.page_location,
                'page_title': row.page_title,
                'engagement_time_ms': row.engagement_time_ms,
                'source': row.source,
                'medium': row.medium,
                'device_category': row.device_category,
                'country': row.country,
            }

            # Derive page_path from page_location
            event['page_path'] = normalize_url_to_path(event['page_location'])

            # Generate event_hash for deduplication
            event['event_hash'] = generate_event_hash(event)

            events.append(event)

        print(f"[OK] Fetched {len(events)} events from BigQuery")
        return events

    except Exception as e:
        print(f"[ERROR] BigQuery query failed: {e}")
        return []

# ============================================================================
# POSTGRES FUNCTIONS
# ============================================================================

def insert_events_to_postgres(conn, events):
    """
    Insert events to Postgres in batches with deduplication.

    Args:
        conn: psycopg2 connection
        events: list of dicts

    Returns: (inserted_count, skipped_count)
    """
    if not events:
        return 0, 0

    cursor = conn.cursor()

    # Prepare data for execute_values
    # Columns: event_hash, event_date, event_timestamp, event_name, user_pseudo_id,
    #          ga_session_id, page_location, page_path, page_title,
    #          source, medium, device_category, country, engagement_time_ms

    insert_query = """
    INSERT INTO sofia.analytics_events (
        event_hash,
        event_date,
        event_timestamp,
        event_name,
        user_pseudo_id,
        ga_session_id,
        page_location,
        page_path,
        page_title,
        source,
        medium,
        device_category,
        country,
        engagement_time_ms
    ) VALUES %s
    ON CONFLICT (event_hash) DO NOTHING
    """

    inserted_count = 0
    skipped_count = 0

    # Process in batches
    for i in range(0, len(events), BATCH_SIZE):
        batch = events[i:i + BATCH_SIZE]

        # Prepare values
        values = []
        for event in batch:
            values.append((
                event['event_hash'],
                event['event_date'],
                event['event_timestamp'],
                event['event_name'],
                event['user_pseudo_id'],
                event['ga_session_id'],
                event['page_location'],
                event['page_path'],
                event['page_title'],
                event['source'],
                event['medium'],
                event['device_category'],
                event['country'],
                event['engagement_time_ms'],
            ))

        try:
            # Execute batch insert
            execute_values(cursor, insert_query, values)
            rows_affected = cursor.rowcount

            inserted_count += rows_affected
            skipped_count += len(batch) - rows_affected

            conn.commit()

            print(f"[BATCH] Inserted {rows_affected}/{len(batch)} (batch {i // BATCH_SIZE + 1})")

        except Exception as e:
            print(f"[ERROR] Batch insert failed: {e}")
            conn.rollback()
            continue

    cursor.close()

    return inserted_count, skipped_count

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Collect GA4 events from BigQuery export to Postgres',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect last 7 days (default)
  python collect_ga4_bigquery.py

  # Collect last 30 days
  python collect_ga4_bigquery.py --days 30

  # Collect specific date range
  python collect_ga4_bigquery.py --start 2026-01-01 --end 2026-01-31

  # Include intraday tables (for today's incomplete data)
  python collect_ga4_bigquery.py --days 1 --include_intraday

Environment Variables:
  GCP_PROJECT_ID=tiespecialistas-tts
  GA4_BQ_DATASET=analytics_xxxxx (optional, auto-detects if not set)
  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME (Postgres config)
        """
    )

    parser.add_argument('--days', type=int, default=7, help='Number of days to collect (default: 7)')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--project', type=str, default=GCP_PROJECT_ID, help='GCP project ID')
    parser.add_argument('--dataset', type=str, default=GA4_BQ_DATASET, help='GA4 BigQuery dataset (auto-detect if not set)')
    parser.add_argument('--include_intraday', action='store_true', help='Include intraday tables (default: false)')

    args = parser.parse_args()

    print("=" * 80)
    print("GA4 BIGQUERY COLLECTOR")
    print("=" * 80)
    print()

    # Calculate date range
    if args.start and args.end:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
    else:
        end_date = datetime.now().date() - timedelta(days=1)  # Yesterday (GA4 exports with 1-day lag)
        start_date = end_date - timedelta(days=args.days - 1)

    print(f"Date Range: {start_date} to {end_date} ({(end_date - start_date).days + 1} days)")
    print(f"Project: {args.project}")
    print(f"Include Intraday: {args.include_intraday}")
    print()

    # Initialize BigQuery client
    try:
        bq_client = bigquery.Client(project=args.project)
        print("[OK] BigQuery client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize BigQuery client: {e}")
        print()
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set:")
        print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
        sys.exit(1)

    # Detect or use dataset
    if args.dataset:
        dataset_id = args.dataset
        print(f"[INFO] Using dataset: {dataset_id}")
    else:
        dataset_id = detect_ga4_dataset(bq_client, args.project)

        if not dataset_id:
            print("[ERROR] No GA4 dataset found. Set GA4_BQ_DATASET or use --dataset")
            sys.exit(1)

        print(f"[INFO] Auto-detected dataset: {dataset_id}")

    print()

    # Fetch events from BigQuery
    events = fetch_events_from_bigquery(
        bq_client,
        args.project,
        dataset_id,
        start_date,
        end_date,
        include_intraday=args.include_intraday
    )

    if not events:
        print()
        print("[WARNING] No events fetched. Exiting.")
        sys.exit(0)

    print()

    # Connect to Postgres
    try:
        pg_conn = psycopg2.connect(**DB_CONFIG)
        print("[OK] Connected to Postgres")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Postgres: {e}")
        sys.exit(1)

    print()

    # Insert events
    print("[INFO] Inserting events to Postgres...")
    inserted, skipped = insert_events_to_postgres(pg_conn, events)

    pg_conn.close()

    print()
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Fetched from BigQuery: {len(events)} events")
    print(f"Inserted to Postgres:  {inserted} events")
    print(f"Skipped (duplicates):  {skipped} events")
    print()

    if inserted > 0:
        print("[OK] Collection successful")
    elif skipped == len(events):
        print("[INFO] All events already exist (idempotent)")
    else:
        print("[WARNING] No events inserted")

if __name__ == '__main__':
    main()
