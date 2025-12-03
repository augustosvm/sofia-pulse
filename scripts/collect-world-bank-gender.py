#!/usr/bin/env python3
"""
World Bank Gender Data Collector
Coleta indicadores de gênero: participação feminina, gap salarial, educação

API: https://api.worldbank.org/v2/
Portal: https://genderdata.worldbank.org/
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

# Gender indicators to collect
# Reference: https://genderdata.worldbank.org/
GENDER_INDICATORS = {
    # Labor force participation
    'SL.TLF.CACT.FE.ZS': 'Labor force participation rate, female (% ages 15+)',
    'SL.TLF.CACT.MA.ZS': 'Labor force participation rate, male (% ages 15+)',

    # Employment
    'SL.EMP.TOTL.SP.FE.ZS': 'Employment to population ratio, female (%)',
    'SL.EMP.TOTL.SP.MA.ZS': 'Employment to population ratio, male (%)',
    'SL.EMP.VULN.FE.ZS': 'Vulnerable employment, female (% of female employment)',

    # Education
    'SE.ENR.TERT.FM.ZS': 'School enrollment, tertiary (gross), gender parity index',
    'SE.ADT.LITR.FE.ZS': 'Literacy rate, adult female (%)',
    'SE.ADT.LITR.MA.ZS': 'Literacy rate, adult male (%)',

    # Management and leadership
    'SG.GEN.PARL.ZS': 'Proportion of seats held by women in national parliaments (%)',
    'IC.FRM.FEMO.ZS': 'Firms with female top manager (% of firms)',
    'IC.FRM.FEMM.ZS': 'Firms with female participation in ownership (%)',

    # Violence and rights
    'SG.VAW.1549.ZS': 'Women who have experienced physical/sexual violence (%)',
    'SG.VAW.AFSX.ZS': 'Women who believe husband is justified in beating wife (%)',

    # Financial inclusion
    'FX.OWN.TOTL.FE.ZS': 'Account ownership at financial institution, female (%)',
    'FX.OWN.TOTL.MA.ZS': 'Account ownership at financial institution, male (%)',
}

# Countries to collect (major economies + Latin America)
COUNTRIES = [
    'BRA', 'USA', 'CHN', 'DEU', 'JPN', 'GBR', 'FRA', 'IND', 'ITA', 'CAN',
    'ARG', 'MEX', 'COL', 'CHL', 'PER', 'VEN', 'ECU', 'URY', 'PRY', 'BOL',
    'ZAF', 'NGA', 'EGY', 'AUS', 'KOR', 'ESP', 'NLD', 'CHE', 'SWE', 'NOR'
]


def fetch_indicator(indicator_code: str, countries: List[str]) -> List[Dict]:
    """Fetch indicator data from World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ';'.join(countries)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {
        'format': 'json',
        'per_page': 1000,
        'date': '2015:2024',  # Last 10 years
        'source': 2  # World Development Indicators
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        # World Bank API returns [metadata, data]
        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception as e:
        print(f"   ❌ Error fetching {indicator_code}: {e}")
        return []


def save_to_database(conn, records: List[Dict], indicator_code: str, indicator_name: str) -> int:
    """Save gender data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.gender_indicators (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(100) DEFAULT 'World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gender_indicator_year
        ON sofia.gender_indicators(indicator_code, year DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gender_country
        ON sofia.gender_indicators(country_code, year DESC)
    """)

    inserted = 0

    for record in records:
        if record.get('value') is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.gender_indicators
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
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("="*80)
    print("📊 WORLD BANK GENDER DATA PORTAL")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://genderdata.worldbank.org/")
    print("")

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print(f"📊 Fetching {len(GENDER_INDICATORS)} gender indicators...")
    print(f"🌍 Countries: {len(COUNTRIES)}")
    print("")

    for indicator_code, indicator_name in GENDER_INDICATORS.items():
        print(f"📈 {indicator_name[:50]}...")

        # Fetch data
        records = fetch_indicator(indicator_code, COUNTRIES)

        if records:
            print(f"   ✅ Fetched: {len(records)} records")

            # Save to database
            inserted = save_to_database(conn, records, indicator_code, indicator_name)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data")

        print("")

    conn.close()

    print("="*80)
    print("✅ WORLD BANK GENDER COLLECTION COMPLETE")
    print("="*80)
    print("")
    print(f"📊 Total indicators: {len(GENDER_INDICATORS)}")
    print(f"🌍 Total countries: {len(COUNTRIES)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Use cases:")
    print("  • Compare gender gap across countries")
    print("  • Track progress on women's participation")
    print("  • Correlate with economic development")


if __name__ == '__main__':
    main()
