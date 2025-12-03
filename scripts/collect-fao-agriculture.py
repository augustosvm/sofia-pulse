#!/usr/bin/env python3
"""
FAO (Food and Agriculture Organization) Data Collector
Coleta dados de agricultura, alimentos, pecuária, pesca

API: https://www.fao.org/faostat/en/#data
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

# FAO indicators (via World Bank API which aggregates FAO data)
FAO_INDICATORS = {
    # Food production
    'AG.PRD.FOOD.XD': 'Food production index (2014-2016 = 100)',
    'AG.PRD.CROP.XD': 'Crop production index (2014-2016 = 100)',
    'AG.PRD.LVSK.XD': 'Livestock production index (2014-2016 = 100)',

    # Land use
    'AG.LND.AGRI.ZS': 'Agricultural land (% of land area)',
    'AG.LND.ARBL.ZS': 'Arable land (% of land area)',
    'AG.LND.FRST.ZS': 'Forest area (% of land area)',

    # Food security
    'SN.ITK.DEFC.ZS': 'Prevalence of undernourishment (%)',
    'SN.ITK.SVFI.ZS': 'Prevalence of severe food insecurity (%)',

    # Agricultural inputs
    'AG.CON.FERT.ZS': 'Fertilizer consumption (kg per hectare)',
    'AG.LND.IRIG.AG.ZS': 'Agricultural irrigated land (%)',

    # Agricultural trade
    'TM.VAL.FOOD.ZS.UN': 'Food imports (% of merchandise imports)',
    'TX.VAL.FOOD.ZS.UN': 'Food exports (% of merchandise exports)',

    # Rural development
    'SP.RUR.TOTL.ZS': 'Rural population (% of total)',
    'NV.AGR.TOTL.ZS': 'Agriculture, value added (% of GDP)',
    'SL.AGR.EMPL.ZS': 'Employment in agriculture (%)',

    # Water
    'ER.H2O.FWAG.ZS': 'Freshwater withdrawal for agriculture (%)',
    'AG.LND.PRCP.MM': 'Average precipitation (mm per year)',
}

COUNTRIES = ['BRA', 'USA', 'CHN', 'IND', 'ARG', 'FRA', 'DEU', 'AUS', 'CAN', 'IDN',
             'RUS', 'UKR', 'THA', 'VNM', 'MEX', 'NGA', 'PAK', 'TUR', 'POL', 'ESP']


def fetch_fao_data(indicator_code: str) -> List[Dict]:
    """Fetch FAO data via World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ';'.join(COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {
        'format': 'json',
        'per_page': 1000,
        'date': '2010:2024',
        'source': 2
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def save_to_database(conn, records: List[Dict], indicator_code: str, indicator_name: str) -> int:
    """Save FAO data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.fao_agriculture_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(50) DEFAULT 'FAO/World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fao_indicator_year
        ON sofia.fao_agriculture_data(indicator_code, year DESC)
    """)

    inserted = 0

    for record in records:
        if record.get('value') is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.fao_agriculture_data
                (indicator_code, indicator_name, country_code, country_name, year, value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, year)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                indicator_code,
                indicator_name,
                record.get('countryiso3code', record.get('country', {}).get('id')),
                record.get('country', {}).get('value'),
                int(record.get('date')) if record.get('date') else None,
                float(record.get('value'))
            ))
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("="*80)
    print("📊 FAO - Food and Agriculture Organization")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://www.fao.org/faostat/")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print(f"📊 Fetching {len(FAO_INDICATORS)} agriculture indicators...")
    print("")

    for indicator_code, indicator_name in FAO_INDICATORS.items():
        print(f"📈 {indicator_name[:50]}...")

        records = fetch_fao_data(indicator_code)

        if records:
            print(f"   ✅ Fetched: {len(records)} records")
            inserted = save_to_database(conn, records, indicator_code, indicator_name)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data")

        print("")

    conn.close()

    print("="*80)
    print("✅ FAO AGRICULTURE COLLECTION COMPLETE")
    print("="*80)
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Topics covered:")
    print("  • Food production indices")
    print("  • Land use and agriculture")
    print("  • Food security")
    print("  • Agricultural trade")
    print("  • Rural development")


if __name__ == '__main__':
    main()
