#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
ILOSTAT (International Labour Organization) Collector
Coleta dados de trabalho: emprego, desemprego, salários, gap salarial

API: https://ilostat.ilo.org/data/
Bulk: https://ilostat.ilo.org/data/bulk/
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

# ILO Indicators (SDMX codes)
ILO_INDICATORS = [
    # Employment
    {'code': 'EMP_TEMP_SEX_AGE_NB', 'name': 'Employment by sex and age', 'category': 'employment'},
    {'code': 'EMP_2EMP_SEX_ECO_NB', 'name': 'Employment by economic activity', 'category': 'employment'},
    {'code': 'EMP_NIFL_SEX_RT', 'name': 'Informal employment rate', 'category': 'employment'},

    # Unemployment
    {'code': 'UNE_TUNE_SEX_AGE_NB', 'name': 'Unemployment by sex and age', 'category': 'unemployment'},
    {'code': 'UNE_2UNE_SEX_AGE_RT', 'name': 'Unemployment rate', 'category': 'unemployment'},
    {'code': 'UNE_DEAP_SEX_AGE_RT', 'name': 'Youth unemployment rate', 'category': 'unemployment'},

    # Wages and earnings
    {'code': 'EAR_4MTH_SEX_ECO_CUR_NB', 'name': 'Mean monthly earnings', 'category': 'wages'},
    {'code': 'EAR_XEES_SEX_ECO_NB', 'name': 'Earnings by economic activity', 'category': 'wages'},

    # Working conditions
    {'code': 'HOW_TEMP_SEX_ECO_NB', 'name': 'Hours worked by sex', 'category': 'conditions'},
    {'code': 'INJ_FATL_ECO_NB', 'name': 'Fatal occupational injuries', 'category': 'safety'},

    # Labor force
    {'code': 'EAP_TEAP_SEX_AGE_NB', 'name': 'Labor force by sex and age', 'category': 'labor_force'},
    {'code': 'EAP_2WAP_SEX_AGE_RT', 'name': 'Labor force participation rate', 'category': 'labor_force'},
]

COUNTRIES = ['BRA', 'USA', 'CHN', 'DEU', 'JPN', 'GBR', 'FRA', 'IND', 'MEX', 'ARG',
             'COL', 'CHL', 'PER', 'ZAF', 'NGA', 'EGY', 'IDN', 'TUR', 'RUS', 'KOR']


def fetch_ilo_data(indicator_code: str) -> List[Dict]:
    """Fetch data from ILOSTAT SDMX API"""

    # SDMX API endpoint
    base_url = "https://www.ilo.org/sdmx/rest"

    url = f"{base_url}/data/ILO,DF_{indicator_code}/....."
    params = {
        'startPeriod': '2018',
        'endPeriod': '2024',
        'detail': 'dataonly',
        'format': 'jsondata'
    }

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Sofia-Pulse-Collector/1.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()

        # Parse SDMX-JSON format
        if 'dataSets' in data and data['dataSets']:
            observations = data['dataSets'][0].get('observations', {})
            structure = data.get('structure', {}).get('dimensions', {}).get('observation', [])

            records = []
            for key, values in observations.items():
                if values and len(values) > 0:
                    records.append({
                        'key': key,
                        'value': values[0],
                        'indicator': indicator_code
                    })
            return records

        return []

    except Exception as e:
        print(f"   ⚠️  SDMX Error: {e}")
        return fetch_ilo_bulk_sample(indicator_code)


def fetch_ilo_bulk_sample(indicator_code: str) -> List[Dict]:
    """Fetch sample data from ILO bulk download"""

    # Try simplified API endpoint
    url = f"https://ilostat.ilo.org/data/bulk/{indicator_code}.csv.gz"

    try:
        # For demo, return empty - bulk requires gzip handling
        return []
    except:
        return []


def save_to_database(conn, records: List[Dict], indicator: Dict) -> int:
    """Save ILO data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.ilo_labor_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            country_code VARCHAR(10),
            sex VARCHAR(20),
            age_group VARCHAR(50),
            economic_activity VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            unit VARCHAR(50),
            source VARCHAR(50) DEFAULT 'ILO',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, sex, age_group, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ilo_indicator_year
        ON sofia.ilo_labor_data(indicator_code, year DESC)
    """)

    inserted = 0

    for record in records:
        value = record.get('value')
        if value is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.ilo_labor_data
                (indicator_code, indicator_name, category, country_code, sex,
                 age_group, year, value, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, sex, age_group, year)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                indicator['code'],
                indicator['name'],
                indicator['category'],
                record.get('country', 'WLD'),
                record.get('sex', 'TOTAL'),
                record.get('age', 'ALL'),
                record.get('year', 2023),
                float(value),
                record.get('unit', '')
            ))
            inserted += 1
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("="*80)
    print("📊 ILOSTAT - International Labour Organization Statistics")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://ilostat.ilo.org/")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print(f"📊 Fetching {len(ILO_INDICATORS)} labor indicators...")
    print("")

    for indicator in ILO_INDICATORS:
        print(f"📈 {indicator['name']} ({indicator['category']})")

        records = fetch_ilo_data(indicator['code'])

        if records:
            print(f"   ✅ Fetched: {len(records)} records")
            inserted = save_to_database(conn, records, indicator)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data via API")

        print("")

    conn.close()

    print("="*80)
    print("✅ ILOSTAT COLLECTION COMPLETE")
    print("="*80)
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 For full data access, use bulk download:")
    print("   https://ilostat.ilo.org/data/bulk/")


if __name__ == '__main__':
    main()
