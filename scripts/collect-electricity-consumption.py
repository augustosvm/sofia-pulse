#!/usr/bin/env python3
"""
Sofia Pulse - Electricity Consumption Collector
Collects global electricity consumption data from EIA API
"""

import os
import sys
import requests
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

# EIA API - FREE (requires registration at https://www.eia.gov/opendata/register.php)
EIA_API_KEY = os.getenv('EIA_API_KEY', '')  # Optional - fallback to CSV if not available

def fetch_eia_data() -> List[Dict[str, Any]]:
    """Fetch electricity consumption data from EIA API or fallback to Our World in Data CSV"""

    if EIA_API_KEY:
        print("📡 Fetching from EIA API...")
        try:
            # EIA International Energy Data - Electricity Consumption
            url = f"https://api.eia.gov/v2/international/data/?api_key={EIA_API_KEY}"
            params = {
                'frequency': 'annual',
                'data[0]': 'value',
                'facets[activityId][]': '2',  # Electricity consumption
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'length': 5000
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'response' in data and 'data' in data['response']:
                print(f"✅ Fetched {len(data['response']['data'])} records from EIA API")
                return data['response']['data']
        except Exception as e:
            print(f"⚠️  EIA API failed: {e}, falling back to CSV...")

    # Fallback to Our World in Data CSV
    print("📥 Downloading Our World in Data - Energy...")
    csv_url = "https://github.com/owid/energy-data/raw/master/owid-energy-data.csv"

    try:
        response = requests.get(csv_url, timeout=60)
        response.raise_for_status()
        print(f"✅ Downloaded {len(response.content)} bytes")

        # Save to temp file and read with pandas
        temp_file = '/tmp/owid-energy.csv'
        with open(temp_file, 'wb') as f:
            f.write(response.content)

        df = pd.read_csv(temp_file)
        print(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")

        # Filter to latest year per country with electricity consumption data
        df = df[df['electricity_demand'].notna()].copy()
        df = df.sort_values('year', ascending=False)
        latest_df = df.groupby('country', as_index=False).first()

        print(f"✅ Filtered to {len(latest_df)} countries with electricity consumption data")

        # Convert to list of dicts
        records = []
        for _, row in latest_df.iterrows():
            records.append({
                'country': row['country'],
                'year': int(row['year']) if pd.notna(row['year']) else None,
                'iso_code': row.get('iso_code'),
                'electricity_demand': float(row['electricity_demand']) if pd.notna(row['electricity_demand']) else None,
                'electricity_generation': float(row.get('electricity_generation', 0)) if pd.notna(row.get('electricity_generation')) else None,
                'per_capita': float(row.get('per_capita_electricity', 0)) if pd.notna(row.get('per_capita_electricity')) else None,
                'population': int(row.get('population', 0)) if pd.notna(row.get('population')) else None,
            })

        return records

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

def safe_float(value, max_value=None):
    """Safely convert to float, handling None and max values"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        float_val = float(value)
        if max_value and abs(float_val) > max_value:
            return None
        return float_val
    except (ValueError, TypeError):
        return None

def safe_int(value, max_value=9223372036854775807):
    """Safely convert to int, handling None and out-of-range values"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        int_val = int(value)
        if abs(int_val) > max_value:
            return None
        return int_val
    except (ValueError, OverflowError):
        return None

def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert electricity consumption data to PostgreSQL"""

    if not records:
        print("⚠️  No records to insert")
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Prepare data for insertion
        insert_query = """
            INSERT INTO sofia.electricity_consumption
            (country, year, iso_code, consumption_twh, generation_twh,
             per_capita_kwh, population, data_source, collected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (country, year)
            DO UPDATE SET
                consumption_twh = EXCLUDED.consumption_twh,
                generation_twh = EXCLUDED.generation_twh,
                per_capita_kwh = EXCLUDED.per_capita_kwh,
                population = EXCLUDED.population,
                data_source = EXCLUDED.data_source,
                updated_at = CURRENT_TIMESTAMP
        """

        data_source = 'EIA' if EIA_API_KEY else 'Our World in Data'

        batch_data = []
        for record in records:
            batch_data.append((
                record.get('country'),
                safe_int(record.get('year')),
                record.get('iso_code'),
                safe_float(record.get('electricity_demand'), max_value=99999999.99),  # DECIMAL(10,2)
                safe_float(record.get('electricity_generation'), max_value=99999999.99),
                safe_float(record.get('per_capita'), max_value=999999.99),  # DECIMAL(8,2)
                safe_int(record.get('population')),
                data_source,
            ))

        execute_batch(cur, insert_query, batch_data, page_size=100)
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
    print("⚡ ELECTRICITY CONSUMPTION COLLECTOR")
    print("=" * 80)
    print()

    # Fetch data
    records = fetch_eia_data()

    if not records:
        print("❌ No data fetched")
        sys.exit(1)

    # Insert to database
    inserted = insert_to_db(records)

    print()
    print("=" * 80)
    print(f"✅ COMPLETE - Inserted {inserted} records")
    print("=" * 80)

if __name__ == '__main__':
    main()
