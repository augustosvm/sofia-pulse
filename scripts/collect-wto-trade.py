#!/usr/bin/env python3
"""
WTO (World Trade Organization) Data Collector
Coleta dados de comércio internacional, tarifas, importação/exportação

API: https://apiportal.wto.org/
Dados: https://stats.wto.org/
"""

import os
import sys
import psycopg2
import requests
from datetime import datetime
from typing import List, Dict, Any

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'sofia')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'sofia_db'))
}

# WTO Indicators
WTO_INDICATORS = [
    # Merchandise trade
    {'code': 'MT_MERCH_TVAL', 'name': 'Total merchandise trade value', 'category': 'merchandise'},
    {'code': 'MT_MERCH_XVAL', 'name': 'Merchandise exports', 'category': 'merchandise'},
    {'code': 'MT_MERCH_MVAL', 'name': 'Merchandise imports', 'category': 'merchandise'},

    # Trade in services
    {'code': 'TS_COMM_SERV_XP', 'name': 'Commercial services exports', 'category': 'services'},
    {'code': 'TS_COMM_SERV_MP', 'name': 'Commercial services imports', 'category': 'services'},

    # Tariffs
    {'code': 'TF_AVG_APLD', 'name': 'Average applied tariff rate', 'category': 'tariffs'},
    {'code': 'TF_AVG_MFN', 'name': 'Average MFN tariff rate', 'category': 'tariffs'},
]

# Countries (WTO member codes)
COUNTRIES = ['BRA', 'USA', 'CHN', 'DEU', 'JPN', 'GBR', 'FRA', 'IND', 'ITA', 'CAN',
             'ARG', 'MEX', 'KOR', 'ESP', 'NLD', 'AUS', 'RUS', 'IDN', 'TUR', 'CHE']


def fetch_wto_data(indicator_code: str) -> List[Dict]:
    """Fetch data from WTO Timeseries API"""

    # WTO API base URL
    base_url = "https://api.wto.org/timeseries/v1"

    url = f"{base_url}/data"
    params = {
        'i': indicator_code,
        'r': ','.join(COUNTRIES),
        'ps': '2018-2024',  # Last 6 years
        'fmt': 'json',
        'mode': 'full',
        'dec': 2,
        'off': 0,
        'max': 5000
    }

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Sofia-Pulse-Collector/1.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=60)

        # WTO API may require registration - try alternative endpoint
        if response.status_code == 401:
            print(f"   ⚠️  WTO API requires registration, trying public stats...")
            return fetch_wto_stats_public(indicator_code)

        response.raise_for_status()
        data = response.json()

        if 'Dataset' in data:
            return data['Dataset']
        return data if isinstance(data, list) else []

    except Exception as e:
        # Try public stats as fallback
        return fetch_wto_stats_public(indicator_code)


def fetch_wto_stats_public(indicator_code: str) -> List[Dict]:
    """Fetch from WTO Stats public endpoint (no auth required)"""

    # This endpoint provides bulk data without authentication
    url = "https://stats.wto.org/api/v1/data"

    try:
        params = {
            'indicators': indicator_code,
            'reportingEconomies': ','.join(COUNTRIES[:10]),
            'years': '2020,2021,2022,2023',
        }

        response = requests.get(url, params=params, timeout=60)
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except:
        return []


def save_to_database(conn, records: List[Dict], indicator: Dict) -> int:
    """Save WTO data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.wto_trade_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            reporter_code VARCHAR(10),
            reporter_name VARCHAR(100),
            partner_code VARCHAR(10),
            partner_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 2),
            unit VARCHAR(50),
            source VARCHAR(50) DEFAULT 'WTO',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, reporter_code, partner_code, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_wto_indicator_year
        ON sofia.wto_trade_data(indicator_code, year DESC)
    """)

    inserted = 0

    for record in records:
        value = record.get('Value', record.get('value'))
        if value is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.wto_trade_data
                (indicator_code, indicator_name, category, reporter_code, reporter_name,
                 partner_code, partner_name, year, value, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, reporter_code, partner_code, year)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                indicator['code'],
                indicator['name'],
                indicator['category'],
                record.get('ReportingEconomyCode', record.get('reporter', '')),
                record.get('ReportingEconomy', record.get('reporterName', '')),
                record.get('PartnerEconomyCode', record.get('partner', 'WLD')),
                record.get('PartnerEconomy', record.get('partnerName', 'World')),
                int(record.get('Year', record.get('year', 0))),
                float(value),
                record.get('Unit', 'USD Million')
            ))
            inserted += 1
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("="*80)
    print("📊 WTO - World Trade Organization Data")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://stats.wto.org/")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print(f"📊 Fetching {len(WTO_INDICATORS)} trade indicators...")
    print(f"🌍 Countries: {len(COUNTRIES)}")
    print("")

    for indicator in WTO_INDICATORS:
        print(f"📈 {indicator['name']} ({indicator['category']})")

        records = fetch_wto_data(indicator['code'])

        if records:
            print(f"   ✅ Fetched: {len(records)} records")
            inserted = save_to_database(conn, records, indicator)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data (API may require registration)")

        print("")

    conn.close()

    print("="*80)
    print("✅ WTO TRADE DATA COLLECTION COMPLETE")
    print("="*80)
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Note: Full WTO API access requires registration at:")
    print("   https://apiportal.wto.org/")


if __name__ == '__main__':
    main()
