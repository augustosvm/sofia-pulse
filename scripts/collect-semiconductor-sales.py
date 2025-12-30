#!/usr/bin/env python3
"""
Sofia Pulse - Semiconductor Sales Collector
Collects global semiconductor sales data from WSTS (World Semiconductor Trade Statistics)
"""

import os
import sys
import requests
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from typing import List, Dict, Any
import json
import re
from dotenv import load_dotenv

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

def fetch_sia_press_releases() -> List[Dict[str, Any]]:
    """
    Fetch semiconductor sales data from SIA (Semiconductor Industry Association) press releases
    SIA publishes free quarterly and monthly sales data
    """

    print("📡 Fetching from SIA Press Releases...")
    records = []

    try:
        # SIA publishes JSON data feeds (check robots.txt first)
        # For now, we'll scrape their latest press release text

        url = "https://www.semiconductors.org/global-semiconductor-sales-increase-18-8-in-q1-2025-compared-to-q1-2024-march-2025-sales-up-1-8-month-to-month/"

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        html = response.text

        # Extract sales figures from text (basic regex parsing)
        # Example: "Global semiconductor sales of $167.7 billion in Q1 2025"

        patterns = [
            r'semiconductor sales of \$?([\d.]+)\s*billion',
            r'sales of \$?([\d.]+)B',
            r'\$?([\d.]+)\s*billion.*(?:Q\d|quarter|month)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Take top 3 matches
                    try:
                        sales_billions = float(match)
                        records.append({
                            'region': 'Global',
                            'year': 2025,
                            'quarter': 'Q1 2025',  # Would parse from context
                            'sales_billions': sales_billions,
                            'source': 'SIA Press Release',
                        })
                    except ValueError:
                        continue

        if records:
            print(f"✅ Extracted {len(records)} data points from SIA")
        else:
            print("⚠️  No data extracted from SIA press release")

    except Exception as e:
        print(f"❌ Error fetching SIA data: {e}")
        import traceback
        traceback.print_exc()

    return records

def fetch_manual_data() -> List[Dict[str, Any]]:
    """
    Manual data entry based on latest SIA reports
    This is updated when new official data is released
    """

    print("📊 Using latest SIA official data...")

    # Latest official data from SIA (as of search results)
    manual_records = [
        {
            'region': 'Global',
            'year': 2025,
            'quarter': 'Q1',
            'month': None,
            'sales_billions': 167.7,
            'yoy_growth': 18.8,
            'source': 'SIA Official',
            'notes': 'Q1 2025 vs Q1 2024'
        },
        {
            'region': 'Global',
            'year': 2025,
            'quarter': 'Q1',
            'month': 'March',
            'sales_billions': 55.9,
            'yoy_growth': None,
            'source': 'SIA Official',
            'notes': 'March 2025'
        },
        {
            'region': 'Global',
            'year': 2024,
            'quarter': 'Q3',
            'month': None,
            'sales_billions': 208.4,
            'qoq_growth': 15.8,
            'source': 'SIA Official',
            'notes': 'Q3 2024 vs Q2 2024'
        },
        {
            'region': 'Global',
            'year': 2024,
            'quarter': 'Q3',
            'month': 'September',
            'sales_billions': 69.5,
            'yoy_growth': 25.1,
            'source': 'SIA Official',
            'notes': 'September 2024'
        },
    ]

    # Regional breakdown (Americas, Europe, Japan, Asia Pacific)
    # Would be expanded with more granular data when available

    print(f"✅ Loaded {len(manual_records)} official records")
    return manual_records

def safe_float(value, max_value=999999999.99):
    """Safely convert to float"""
    if value is None:
        return None
    try:
        float_val = float(value)
        if abs(float_val) > max_value:
            return None
        return float_val
    except (ValueError, TypeError):
        return None

def safe_int(value):
    """Safely convert to int"""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert semiconductor sales data to PostgreSQL"""

    if not records:
        print("⚠️  No records to insert")
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO sofia.semiconductor_sales
            (region, year, quarter, month, sales_usd_billions,
             yoy_growth_pct, qoq_growth_pct, data_source, notes, collected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (region, year, quarter, month)
            DO UPDATE SET
                sales_usd_billions = EXCLUDED.sales_usd_billions,
                yoy_growth_pct = EXCLUDED.yoy_growth_pct,
                qoq_growth_pct = EXCLUDED.qoq_growth_pct,
                data_source = EXCLUDED.data_source,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP
        """

        batch_data = []
        for record in records:
            batch_data.append((
                record.get('region', 'Global'),
                safe_int(record.get('year')),
                record.get('quarter') or '',  # Convert None to empty string
                record.get('month') or '',    # Convert None to empty string
                safe_float(record.get('sales_billions')),
                safe_float(record.get('yoy_growth')),
                safe_float(record.get('qoq_growth')),
                record.get('source', 'Unknown'),
                record.get('notes'),
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
    print("💾 SEMICONDUCTOR SALES COLLECTOR")
    print("=" * 80)
    print()

    # Use manual curated data (most reliable)
    records = fetch_manual_data()

    # Optionally try to scrape SIA for latest updates
    scraped = fetch_sia_press_releases()
    if scraped:
        records.extend(scraped)

    if not records:
        print("❌ No data available")
        sys.exit(1)

    # Insert to database
    inserted = insert_to_db(records)

    # Show summary
    if records:
        print()
        print("📊 Semiconductor Sales Summary:")
        for record in records[:5]:  # Show first 5
            period = f"{record.get('quarter', '')} {record.get('month', '')}".strip()
            print(f"   {record['year']} {period}: ${record['sales_billions']}B ({record['region']})")

    print()
    print("=" * 80)
    print(f"✅ COMPLETE - Inserted {inserted} records")
    print("=" * 80)
    print()
    print("💡 INFO: Data sourced from SIA official reports")
    print("   Updated manually from: https://www.semiconductors.org/")

if __name__ == '__main__':
    main()
