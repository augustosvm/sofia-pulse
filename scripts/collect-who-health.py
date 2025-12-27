#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
WHO (World Health Organization) Data Collector
Coleta dados de saúde global: doenças, mortalidade, sistemas de saúde

API: https://ghoapi.azureedge.net/api/
Portal: https://www.who.int/data/gho
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

# WHO GHO Indicators
WHO_INDICATORS = [
    # Life expectancy
    {'code': 'WHOSIS_000001', 'name': 'Life expectancy at birth', 'category': 'mortality'},
    {'code': 'WHOSIS_000002', 'name': 'Healthy life expectancy at birth', 'category': 'mortality'},

    # Mortality
    {'code': 'MORT_MATERNALNUM', 'name': 'Maternal deaths', 'category': 'mortality'},
    {'code': 'MDG_0000000001', 'name': 'Maternal mortality ratio', 'category': 'mortality'},
    {'code': 'NCDMORT3070', 'name': 'NCD mortality rate (30-70)', 'category': 'mortality'},

    # Disease burden
    {'code': 'MALARIA_EST_INCIDENCE', 'name': 'Malaria incidence', 'category': 'disease'},
    {'code': 'TB_e_inc_num', 'name': 'TB incidence', 'category': 'disease'},
    {'code': 'HIV_0000000001', 'name': 'HIV prevalence', 'category': 'disease'},

    # Health systems
    {'code': 'HWF_0001', 'name': 'Physicians per 10,000', 'category': 'health_system'},
    {'code': 'HWF_0006', 'name': 'Nurses and midwives per 10,000', 'category': 'health_system'},
    {'code': 'WHS6_102', 'name': 'Hospital beds per 10,000', 'category': 'health_system'},

    # Universal health coverage
    {'code': 'UHC_INDEX_REPORTED', 'name': 'UHC service coverage index', 'category': 'coverage'},

    # Risk factors
    {'code': 'NCD_BMI_30A', 'name': 'Obesity prevalence (BMI>=30)', 'category': 'risk'},
    {'code': 'M_Est_smk_curr_std', 'name': 'Tobacco smoking prevalence', 'category': 'risk'},
    {'code': 'SA_0000001688', 'name': 'Alcohol consumption per capita', 'category': 'risk'},

    # Mental health
    {'code': 'SDGSUICIDE', 'name': 'Suicide mortality rate', 'category': 'mental_health'},
]

COUNTRIES = ['BRA', 'USA', 'CHN', 'IND', 'DEU', 'JPN', 'GBR', 'FRA', 'MEX', 'ARG',
             'NGA', 'ZAF', 'EGY', 'IDN', 'PAK', 'BGD', 'RUS', 'TUR', 'KOR', 'ITA']


def fetch_who_data(indicator_code: str) -> List[Dict]:
    """Fetch data from WHO GHO OData API"""

    base_url = "https://ghoapi.azureedge.net/api"

    url = f"{base_url}/{indicator_code}"
    country_filter = "','".join(COUNTRIES)
    params = {
        '$filter': f"SpatialDim in ('{country_filter}')"
    }

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Sofia-Pulse-Collector/1.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        if 'value' in data:
            return data['value']
        return []

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def save_to_database(conn, records: List[Dict], indicator: Dict) -> int:
    """Save WHO data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.who_health_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            country_code VARCHAR(10),
            sex VARCHAR(20),
            year INTEGER,
            value DECIMAL(18, 6),
            value_type VARCHAR(50),
            source VARCHAR(50) DEFAULT 'WHO',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, sex, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_who_indicator_year
        ON sofia.who_health_data(indicator_code, year DESC)
    """)

    inserted = 0

    for record in records:
        value = record.get('NumericValue')
        if value is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.who_health_data
                (indicator_code, indicator_name, category, country_code, sex, year, value, value_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, sex, year)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                indicator['code'],
                indicator['name'],
                indicator['category'],
                record.get('SpatialDim', ''),
                record.get('Dim1', 'BTSX'),
                int(record.get('TimeDim', 0)) if record.get('TimeDim') else None,
                float(value),
                record.get('Dim1Type', '')
            ))
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("="*80)
    print("📊 WHO - World Health Organization Global Health Observatory")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://www.who.int/data/gho")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print(f"📊 Fetching {len(WHO_INDICATORS)} health indicators...")
    print("")

    for indicator in WHO_INDICATORS:
        print(f"📈 {indicator['name']} ({indicator['category']})")

        records = fetch_who_data(indicator['code'])

        if records:
            print(f"   ✅ Fetched: {len(records)} records")
            inserted = save_to_database(conn, records, indicator)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data")

        print("")

    conn.close()

    print("="*80)
    print("✅ WHO HEALTH DATA COLLECTION COMPLETE")
    print("="*80)
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Topics covered:")
    print("  • Life expectancy")
    print("  • Maternal mortality")
    print("  • Disease burden (TB, HIV, Malaria)")
    print("  • Health workforce")
    print("  • Risk factors")


if __name__ == '__main__':
    main()
