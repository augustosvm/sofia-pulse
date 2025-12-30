#!/usr/bin/env python3
"""
Sofia Pulse - Commodity Prices Collector
Collects current prices for major commodities (oil, gold, copper, wheat, etc.)
"""

import os
import sys
from typing import Any, Dict, List

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

# API Ninjas - FREE (get key at https://api-ninjas.com/api/commodityprice)
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY", "")

# Free tier commodities - most commodities require premium plan
# Only platinum is confirmed to work on free tier
FREE_TIER_COMMODITIES = [
    "platinum",
]

# Premium commodities (require paid plan) - used for fallback data
PREMIUM_COMMODITIES = [
    "crude_oil_wti",
    "crude_oil_brent",
    "gold",
    "copper",
]


def fetch_api_ninjas() -> List[Dict[str, Any]]:
    """Fetch commodity prices from API Ninjas (free tier only)"""

    if not API_NINJAS_KEY:
        print("⚠️  API_NINJAS_KEY not set, skipping API Ninjas")
        return []

    print("📡 Fetching from API Ninjas (free tier)...")
    records = []

    for commodity in FREE_TIER_COMMODITIES:
        try:
            url = f"https://api.api-ninjas.com/v1/commodityprice?name={commodity}"
            headers = {"X-Api-Key": API_NINJAS_KEY}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and "price" in data:
                    records.append(
                        {
                            "commodity": data.get("name", commodity),
                            "price": float(data["price"]),
                            "unit": data.get("unit", "USD"),
                            "source": "API Ninjas",
                        }
                    )
                    print(f"   ✅ {commodity}: ${data['price']}")
            else:
                print(f"   ⚠️  {commodity}: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ {commodity}: {e}")
            continue

    if records:
        print(f"✅ Fetched {len(records)} commodities from API Ninjas")
    else:
        print("⚠️  No free tier commodities available, using fallback...")

    return records


def fetch_fallback_prices() -> List[Dict[str, Any]]:
    """Fallback: Return placeholder data for premium commodities"""

    print("📡 Using fallback data for premium commodities...")
    records = []

    try:
        # Placeholder data for premium commodities (approximate Q4 2024 prices)
        # These require API Ninjas premium plan or alternative data source
        fallback_commodities = {
            "crude_oil_wti": {"price": 76.20, "unit": "USD/barrel", "note": "Q4 2024 avg"},
            "crude_oil_brent": {"price": 79.80, "unit": "USD/barrel", "note": "Q4 2024 avg"},
            "gold": {"price": 2068.00, "unit": "USD/oz", "note": "Q4 2024 avg"},
            "copper": {"price": 4.15, "unit": "USD/lb", "note": "Q4 2024 avg"},
        }

        print("⚠️  Using placeholder data (Q4 2024 averages)")
        print("   💡 Upgrade to API Ninjas premium for real-time prices")
        print("   📝 Or use alternative APIs: commodities-api.com, alphavantage.co")

        for name, data in fallback_commodities.items():
            records.append(
                {
                    "commodity": name,
                    "price": data["price"],
                    "unit": data["unit"],
                    "source": "Placeholder (Q4 2024)",
                }
            )
            print(f"   📊 {name}: ${data['price']} {data['unit']} ({data['note']})")

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
            batch_data.append(
                (
                    record.get("commodity"),
                    safe_float(record.get("price")),
                    record.get("unit", "USD"),
                    record.get("source", "Unknown"),
                )
            )

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

    # Fetch free tier data from API Ninjas
    api_records = fetch_api_ninjas() if API_NINJAS_KEY else []

    print()

    # Always add fallback data for premium commodities
    fallback_records = fetch_fallback_prices()

    # Deduplicate: prioritize API real over fallback
    seen_commodities = set()
    all_records = []

    # Add API records first (priority)
    for record in api_records:
        commodity = record["commodity"]
        if commodity not in seen_commodities:
            all_records.append(record)
            seen_commodities.add(commodity)

    # Add fallback only for missing commodities
    for record in fallback_records:
        commodity = record["commodity"]
        if commodity not in seen_commodities:
            all_records.append(record)
            seen_commodities.add(commodity)

    if not all_records:
        print("❌ No data fetched")
        sys.exit(1)

    print()

    # Insert to database
    inserted = insert_to_db(all_records)

    # Show summary
    print()
    print("📊 Commodity Prices Summary:")
    api_count = len(api_records)
    fallback_count = len(fallback_records)
    print(f"   Total tracked: {len(all_records)} commodities")
    if api_count > 0:
        print(f"   Real-time (API Ninjas): {api_count}")
    if fallback_count > 0:
        print(f"   Placeholder (Q4 2024): {fallback_count}")

    print()
    print("=" * 80)
    print(f"✅ COMPLETE - Inserted {inserted} records")
    print("=" * 80)
    print()
    print("💡 NOTE: Most commodities require API Ninjas premium plan")
    print("   Free alternative: Alpha Vantage (commodities section)")
    print("   Get key at: https://www.alphavantage.co/support/#api-key")


if __name__ == "__main__":
    main()
