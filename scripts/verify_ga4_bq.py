#!/usr/bin/env python3
"""
GA4 BigQuery Export Verification Script

Detects GA4 dataset, lists tables, and shows sample data.
"""

import os
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def detect_ga4_dataset(client, project_id):
    """
    Detect GA4 dataset by searching for analytics_* patterns.

    Returns: dataset_id or None
    """
    print(f"Scanning for GA4 datasets in project: {project_id}")
    print()

    try:
        datasets = list(client.list_datasets(project_id))

        if not datasets:
            print(f"[WARNING] No datasets found in project {project_id}")
            return None

        ga4_datasets = []

        for dataset in datasets:
            dataset_id = dataset.dataset_id

            # Check if matches GA4 pattern: analytics_<property_id>
            if dataset_id.startswith('analytics_'):
                ga4_datasets.append(dataset_id)
                print(f"[FOUND] GA4 dataset: {dataset_id}")

        if not ga4_datasets:
            print("[WARNING] No analytics_* datasets found")
            print("Available datasets:")
            for dataset in datasets:
                print(f"  - {dataset.dataset_id}")
            return None

        # Return first match (or let user override via ENV)
        selected = ga4_datasets[0]

        if len(ga4_datasets) > 1:
            print(f"\n[INFO] Multiple GA4 datasets found. Using: {selected}")
            print("Override with GA4_BQ_DATASET environment variable if needed.")

        return selected

    except Exception as e:
        print(f"[ERROR] Failed to list datasets: {e}")
        return None

def list_event_tables(client, project_id, dataset_id):
    """
    List events_* tables in the GA4 dataset.

    Returns: list of table_ids
    """
    print(f"\nListing event tables in {project_id}.{dataset_id}...")
    print()

    try:
        dataset_ref = f"{project_id}.{dataset_id}"
        tables = list(client.list_tables(dataset_ref))

        if not tables:
            print("[WARNING] No tables found in dataset")
            return []

        event_tables = []
        intraday_tables = []

        for table in tables:
            table_id = table.table_id

            if table_id.startswith('events_intraday_'):
                intraday_tables.append(table_id)
            elif table_id.startswith('events_'):
                event_tables.append(table_id)

        # Sort by date (newest first)
        event_tables.sort(reverse=True)
        intraday_tables.sort(reverse=True)

        print(f"Event tables (daily): {len(event_tables)}")
        if event_tables:
            print("Latest 5 tables:")
            for table_id in event_tables[:5]:
                # Extract date from events_YYYYMMDD
                date_str = table_id.replace('events_', '')
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    print(f"  - {table_id} ({date_obj.strftime('%Y-%m-%d')})")
                except:
                    print(f"  - {table_id}")

        print()
        print(f"Event tables (intraday): {len(intraday_tables)}")
        if intraday_tables:
            print("Latest 3 tables:")
            for table_id in intraday_tables[:3]:
                print(f"  - {table_id}")

        return event_tables

    except Exception as e:
        print(f"[ERROR] Failed to list tables: {e}")
        return []

def count_events(client, project_id, dataset_id, table_suffix):
    """
    Count events for a specific date.

    Args:
        table_suffix: YYYYMMDD format (e.g., '20260122')

    Returns: count or None
    """
    query = f"""
    SELECT COUNT(*) as event_count
    FROM `{project_id}.{dataset_id}.events_{table_suffix}`
    """

    try:
        query_job = client.query(query)
        result = query_job.result()

        for row in result:
            return row.event_count

        return None

    except Exception as e:
        print(f"[ERROR] Failed to count events for {table_suffix}: {e}")
        return None

def sample_events(client, project_id, dataset_id, table_suffix, limit=5):
    """
    Get sample events from a specific date.

    Returns: list of dicts
    """
    query = f"""
    SELECT
        event_date,
        event_timestamp,
        event_name,
        user_pseudo_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') as page_location,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title') as page_title,
        device.category as device_category,
        geo.country as country,
        traffic_source.source as source,
        traffic_source.medium as medium
    FROM `{project_id}.{dataset_id}.events_{table_suffix}`
    LIMIT {limit}
    """

    try:
        query_job = client.query(query)
        result = query_job.result()

        samples = []
        for row in result:
            samples.append({
                'event_date': row.event_date,
                'event_timestamp': row.event_timestamp,
                'event_name': row.event_name,
                'user_pseudo_id': row.user_pseudo_id,
                'page_location': row.page_location,
                'page_title': row.page_title,
                'device_category': row.device_category,
                'country': row.country,
                'source': row.source,
                'medium': row.medium,
            })

        return samples

    except Exception as e:
        print(f"[ERROR] Failed to fetch sample events: {e}")
        return []

def main():
    print("=" * 80)
    print("GA4 BIGQUERY EXPORT VERIFICATION")
    print("=" * 80)
    print()

    # Get config
    project_id = os.getenv('GCP_PROJECT_ID', 'tiespecialistas-tts')
    dataset_override = os.getenv('GA4_BQ_DATASET')

    print(f"Project ID: {project_id}")
    print(f"GA4 Dataset Override: {dataset_override or '(auto-detect)'}")
    print()

    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
        print(f"[OK] BigQuery client initialized")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to initialize BigQuery client: {e}")
        print()
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set:")
        print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
        sys.exit(1)

    # Detect or use override dataset
    if dataset_override:
        dataset_id = dataset_override
        print(f"[INFO] Using override dataset: {dataset_id}")
        print()
    else:
        dataset_id = detect_ga4_dataset(client, project_id)

        if not dataset_id:
            print()
            print("[ERROR] No GA4 dataset found. Exiting.")
            sys.exit(1)

    print()
    print("-" * 80)

    # List event tables
    event_tables = list_event_tables(client, project_id, dataset_id)

    if not event_tables:
        print()
        print("[ERROR] No event tables found. Is GA4 export configured?")
        print()
        print("To configure GA4 export:")
        print("1. Go to GA4 Admin > Property > BigQuery Links")
        print("2. Link your BigQuery project")
        print("3. Enable daily export (and optionally streaming/intraday)")
        print("4. Wait 24h for first export")
        sys.exit(1)

    print()
    print("-" * 80)

    # Get latest table
    latest_table = event_tables[0]
    table_suffix = latest_table.replace('events_', '')

    print(f"\nAnalyzing latest table: {latest_table}")
    print()

    # Count events
    event_count = count_events(client, project_id, dataset_id, table_suffix)

    if event_count is not None:
        print(f"Total events: {event_count:,}")
    else:
        print("[WARNING] Could not count events")

    print()
    print("-" * 80)

    # Sample events
    print(f"\nSample events (first 5):")
    print()

    samples = sample_events(client, project_id, dataset_id, table_suffix, limit=5)

    if samples:
        for i, event in enumerate(samples, 1):
            print(f"{i}. Event: {event['event_name']}")
            print(f"   Date: {event['event_date']}")
            print(f"   User: {event['user_pseudo_id']}")
            print(f"   Page: {event['page_location']}")
            print(f"   Title: {event['page_title']}")
            print(f"   Device: {event['device_category']}")
            print(f"   Country: {event['country']}")
            print(f"   Source/Medium: {event['source']}/{event['medium']}")
            print()
    else:
        print("[WARNING] No sample events available")

    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Dataset: {project_id}.{dataset_id}")
    print(f"Latest table: {latest_table}")
    print(f"Total tables: {len(event_tables)}")

    if event_count:
        print(f"Latest events: {event_count:,}")

    print()
    print("[OK] GA4 export is working. Ready to run collector.")

if __name__ == '__main__':
    main()
