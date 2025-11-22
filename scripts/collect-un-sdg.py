#!/usr/bin/env python3
"""
UN SDG (Sustainable Development Goals) Collector
Coleta indicadores dos 17 ODS com foco em gênero (ODS 5), desigualdade (ODS 10)

API: https://unstats.un.org/sdgapi/swagger/
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

# SDG Goals to collect (focus on social indicators)
SDG_GOALS = {
    '1': 'No Poverty',
    '3': 'Good Health and Well-being',
    '4': 'Quality Education',
    '5': 'Gender Equality',  # Priority
    '8': 'Decent Work and Economic Growth',
    '10': 'Reduced Inequalities',  # Priority
    '16': 'Peace, Justice and Strong Institutions',
}

# Key SDG indicators
SDG_INDICATORS = [
    # Goal 5 - Gender Equality
    '5.1.1',  # Legal frameworks for gender equality
    '5.2.1',  # Physical/sexual violence by partner
    '5.2.2',  # Sexual violence by non-partner
    '5.3.1',  # Child marriage
    '5.4.1',  # Time spent on unpaid domestic work
    '5.5.1',  # Women in parliament
    '5.5.2',  # Women in managerial positions
    '5.6.1',  # Women making informed decisions on reproductive health

    # Goal 10 - Reduced Inequalities
    '10.1.1',  # Income growth of bottom 40%
    '10.2.1',  # People below 50% median income
    '10.3.1',  # Discrimination experiences
    '10.4.1',  # Labour share of GDP

    # Goal 8 - Decent Work
    '8.5.1',  # Average earnings
    '8.5.2',  # Unemployment rate
    '8.6.1',  # Youth not in employment/education
    '8.8.1',  # Occupational injuries

    # Goal 4 - Education
    '4.1.1',  # Minimum proficiency in reading/math
    '4.2.1',  # Early childhood development
    '4.5.1',  # Gender parity indices
]

# Countries (using M49 codes for some, ISO3 for others)
COUNTRIES = [
    '76',   # Brazil
    '840',  # USA
    '156',  # China
    '276',  # Germany
    '392',  # Japan
    '826',  # UK
    '250',  # France
    '356',  # India
    '380',  # Italy
    '124',  # Canada
    '32',   # Argentina
    '484',  # Mexico
    '170',  # Colombia
    '152',  # Chile
    '604',  # Peru
]


def fetch_sdg_data(indicator: str) -> List[Dict]:
    """Fetch SDG indicator data from UN Stats API"""

    base_url = "https://unstats.un.org/sdgapi/v1"

    # Get data for indicator
    url = f"{base_url}/sdg/Indicator/{indicator}/Data"
    params = {
        'pageSize': 1000,
    }

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Sofia-Pulse-Collector/1.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            return data['data']
        return data if isinstance(data, list) else []

    except Exception as e:
        print(f"   ❌ Error fetching {indicator}: {e}")
        return []


def save_to_database(conn, records: List[Dict], indicator_code: str) -> int:
    """Save SDG data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.sdg_indicators (
            id SERIAL PRIMARY KEY,
            goal VARCHAR(10),
            indicator_code VARCHAR(20) NOT NULL,
            indicator_name TEXT,
            series_code VARCHAR(50),
            series_description TEXT,
            geo_area_code VARCHAR(10),
            geo_area_name VARCHAR(200),
            time_period VARCHAR(20),
            value DECIMAL(18, 6),
            sex VARCHAR(20),
            age VARCHAR(50),
            source VARCHAR(200),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, series_code, geo_area_code, time_period, sex, age)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sdg_goal
        ON sofia.sdg_indicators(goal, time_period DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sdg_indicator
        ON sofia.sdg_indicators(indicator_code, geo_area_code)
    """)

    inserted = 0

    for record in records:
        value = record.get('value')
        if value is None or value == '':
            continue

        try:
            goal = indicator_code.split('.')[0] if '.' in indicator_code else ''

            cursor.execute("""
                INSERT INTO sofia.sdg_indicators
                (goal, indicator_code, indicator_name, series_code, series_description,
                 geo_area_code, geo_area_name, time_period, value, sex, age, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, series_code, geo_area_code, time_period, sex, age)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                goal,
                indicator_code,
                record.get('indicator', [None])[0] if record.get('indicator') else None,
                record.get('seriesCode', record.get('series', '')),
                record.get('seriesDescription', ''),
                record.get('geoAreaCode', ''),
                record.get('geoAreaName', ''),
                str(record.get('timePeriod', record.get('timePeriodStart', ''))),
                float(value),
                record.get('sex', 'BOTHSEX'),
                record.get('age', 'ALLAGE'),
                record.get('source', 'UN SDG')
            ))
            inserted += 1
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("="*80)
    print("📊 UN SDG (Sustainable Development Goals) API")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://unstats.un.org/sdgs/")
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

    print(f"📊 Fetching {len(SDG_INDICATORS)} SDG indicators...")
    print("")
    print("Focus areas:")
    for goal, name in SDG_GOALS.items():
        print(f"  • Goal {goal}: {name}")
    print("")

    for indicator in SDG_INDICATORS:
        goal = indicator.split('.')[0]
        goal_name = SDG_GOALS.get(goal, 'Unknown')
        print(f"📈 Indicator {indicator} ({goal_name[:30]}...)")

        # Fetch data
        records = fetch_sdg_data(indicator)

        if records:
            print(f"   ✅ Fetched: {len(records)} records")

            # Save to database
            inserted = save_to_database(conn, records, indicator)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data")

        print("")

    conn.close()

    print("="*80)
    print("✅ UN SDG COLLECTION COMPLETE")
    print("="*80)
    print("")
    print(f"📊 Total indicators: {len(SDG_INDICATORS)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Key indicators collected:")
    print("  • Gender equality (Goal 5)")
    print("  • Reduced inequalities (Goal 10)")
    print("  • Decent work (Goal 8)")
    print("  • Quality education (Goal 4)")


if __name__ == '__main__':
    main()
