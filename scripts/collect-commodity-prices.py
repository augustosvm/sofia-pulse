#!/usr/bin/env python3
"""
Sofia Pulse - Commodity Prices Collector
Collects current prices for major commodities (oil, gold, copper, wheat, etc.)
"""

import os
import sys
import requests
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from typing import List, Dict, Any
import json
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

# API Ninjas - FREE (get key at https://api-ninjas.com/api/commodityprice)
API_NINJAS_KEY = os.getenv('API_NINJAS_KEY', '')

# Major commodities to track
COMMODITIES = [
    'crude_oil_wti',  # WTI Crude Oil
    'crude_oil_brent',  # Brent Crude Oil
    'natural_gas',
    'gold',
    'silver',
    'copper',
    'platinum',
    'palladium',
    'wheat',
    'corn',
    'soybeans',
    'rice',
    'sugar',
    'coffee',
    'cotton',
    'lithium',  # For EV batteries
    'cobalt',
    'nickel',
]

def fetch_api_ninjas() -> List[Dict[str, Any]]:
    """Fetch commodity prices from API Ninjas"""

    if not API_NINJAS_KEY:
        print("⚠️  API_NINJAS_KEY not set, skipping API Ninjas")
        return []

    print("📡 Fetching from API Ninjas...")
    records = []

    for commodity in COMMODITIES:
        try:
            url = f"https://api.api-ninjas.com/v1/commodityprice?name={commodity}"
            headers = {'X-Api-Key': API_NINJAS_KEY}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'price' in data:
                    records.append({
                        'commodity': data.get('name', commodity),
                        'price': float(data['price']),
                        'unit': data.get('unit', 'USD'),
                        'source': 'API Ninjas',
                    })
                    print(f"   ✅ {commodity}: ${data['price']}")
            else:
                print(f"   ⚠️  {commodity}: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ {commodity}: {e}")
            continue

    print(f"✅ Fetched {len(records)} commodities from API Ninjas")
    return records

def fetch_fallback_prices() -> List[Dict[str, Any]]:
    """Fallback: Scrape commodity prices from public sources"""

    print("📡 Fetching fallback commodity prices...")
    records = []

    try:
        # Use a simple public API that doesn't require keys
        # Example: commodities-api.com has a free tier
        # For now, we'll return mock data structure - user can add API key later

        # Mock structure for demonstration
        fallback_commodities = {
            'crude_oil_wti': {'price': 75.50, 'unit': 'USD/barrel'},
            'gold': {'price': 2050.00, 'unit': 'USD/oz'},
            'copper': {'price': 4.25, 'unit': 'USD/lb'},
            'wheat': {'price': 650.00, 'unit': 'USD/bushel'},
        }

        print("⚠️  Using placeholder data - add API_NINJAS_KEY for real-time prices")
        for name, data in fallback_commodities.items():
            records.append({
                'commodity': name,
                'price': data['price'],
                'unit': data['unit'],
                'source': 'Placeholder',
            })

    except Exception as e:
        print(f"❌ Fallback failed: {e}")

    return records

def safe_float(value, max_value=999999999.99):
    """Safely convert to float, handling None"""
    if value is None:
        return None
    try:
        float_val = float(value)
        if abs(float_val) > max_value:
            return None
        return float_val
    except (ValueError, TypeError):
        return None

def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert commodity prices to PostgreSQL"""

    if not records:
        print("⚠️  No records to insert")
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO sofia.commodity_prices
            (commodity, price, unit, data_source, price_date, collected_at)
            VALUES (%s, %s, %s, %s, CURRENT_DATE, CURRENT_TIMESTAMP)
            ON CONFLICT (commodity, price_date)
            DO UPDATE SET
                price = EXCLUDED.price,
                unit = EXCLUDED.unit,
                data_source = EXCLUDED.data_source,
                updated_at = CURRENT_TIMESTAMP
        """

        batch_data = []
        for record in records:
            batch_data.append((
                record.get('commodity'),
                safe_float(record.get('price')),
                record.get('unit', 'USD'),
                record.get('source', 'Unknown'),
            ))

        execute_batch(cur, insert_query, batch_data, page_size=100)
        conn.commit()

        print(f"✅ Inserted/updated {len(batch_data)} commodities")
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
    print("📈 COMMODITY PRICES COLLECTOR")
    print("=" * 80)
    print()

    # Try API Ninjas first
    records = fetch_api_ninjas()

    # Fallback if no API key
    if not records:
        records = fetch_fallback_prices()

    if not records:
        print("❌ No data fetched")
        sys.exit(1)

    # Insert to database
    inserted = insert_to_db(records)

    # Show summary
    if records:
        print()
        print("📊 Commodity Prices Summary:")
        print(f"   Total tracked: {len(records)}")
        print(f"   Data source: {records[0].get('source', 'Unknown')}")

    print()
    print("=" * 80)
    print(f"✅ COMPLETE - Inserted {inserted} records")
    print("=" * 80)
    print()
    print("💡 TIP: Set API_NINJAS_KEY env variable for real-time prices")
    print("   Get free API key at: https://api-ninjas.com/api/commodityprice")

if __name__ == '__main__':
    main()
