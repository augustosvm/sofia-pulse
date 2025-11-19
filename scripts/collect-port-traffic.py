#!/usr/bin/env python3
"""
Sofia Pulse - Port Traffic Collector
Collects global port container traffic data from World Bank
"""

import os
import sys
import requests
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import json

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

def fetch_worldbank_data() -> List[Dict[str, Any]]:
    """Fetch container port traffic data from World Bank API (FREE)"""

    print("📡 Fetching from World Bank API...")

    try:
        # World Bank Indicator: IS.SHP.GOOD.TU - Container port traffic (TEU: 20 foot equivalent units)
        url = "https://api.worldbank.org/v2/country/all/indicator/IS.SHP.GOOD.TU"
        params = {
            'format': 'json',
            'per_page': 20000,  # Get all data
            'date': '2010:2025'  # Last 15 years
        }

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and isinstance(data[1], list):
            records = []
            for item in data[1]:
                if item.get('value') is not None:  # Only records with actual data
                    records.append({
                        'country': item['country']['value'],
                        'country_code': item['countryiso3code'],
                        'year': int(item['date']),
                        'teu': int(item['value']),
                    })

            print(f"✅ Fetched {len(records)} records from World Bank")
            return records
        else:
            print("❌ Unexpected API response format")
            return []

    except Exception as e:
        print(f"❌ Error fetching World Bank data: {e}")
        import traceback
        traceback.print_exc()
        return []

def safe_bigint(value, max_value=9223372036854775807):
    """Safely convert to bigint, handling None and out-of-range values"""
    if value is None:
        return None
    try:
        int_val = int(value)
        if abs(int_val) > max_value:
            return None
        return int_val
    except (ValueError, OverflowError):
        return None

def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert port traffic data to PostgreSQL"""

    if not records:
        print("⚠️  No records to insert")
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO sofia.port_traffic
            (country, country_code, year, teu, collected_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (country, year)
            DO UPDATE SET
                teu = EXCLUDED.teu,
                country_code = EXCLUDED.country_code,
                updated_at = CURRENT_TIMESTAMP
        """

        batch_data = []
        for record in records:
            batch_data.append((
                record.get('country'),
                record.get('country_code'),
                record.get('year'),
                safe_bigint(record.get('teu')),
            ))

        execute_batch(cur, insert_query, batch_data, page_size=500)
        conn.commit()

        print(f"✅ Inserted/updated {len(batch_data)} records")
        return len(batch_data)

    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return 0
    finally:
        if conn:
            conn.close()

def main():
    print("=" * 80)
    print("🚢 PORT TRAFFIC COLLECTOR")
    print("=" * 80)
    print()

    # Fetch data
    records = fetch_worldbank_data()

    if not records:
        print("❌ No data fetched")
        sys.exit(1)

    # Insert to database
    inserted = insert_to_db(records)

    # Show preview of top ports
    if records:
        print()
        print("📊 Top 10 Container Ports (Latest Year):")
        df = pd.DataFrame(records)
        latest_year = df['year'].max()
        latest = df[df['year'] == latest_year].nlargest(10, 'teu')[['country', 'teu', 'year']]
        for _, row in latest.iterrows():
            print(f"   {row['country']}: {row['teu']:,} TEU ({row['year']})")

    print()
    print("=" * 80)
    print(f"✅ COMPLETE - Inserted {inserted} records")
    print("=" * 80)

if __name__ == '__main__':
    main()
