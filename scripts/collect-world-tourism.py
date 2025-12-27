#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
World Tourism Data Collector
Coleta dados de turismo mundial de fontes oficiais

APIs:
- World Bank Tourism Indicators: https://api.worldbank.org/v2/
- UNWTO Data: https://www.unwto.org/tourism-statistics/key-tourism-statistics
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

# World Bank Tourism Indicators
# Source: https://data.worldbank.org/topic/21 (Private Sector & Trade - Tourism)
TOURISM_INDICATORS = {
    # ===========================================
    # INTERNATIONAL TOURISM
    # ===========================================
    'ST.INT.ARVL': {
        'name': 'International tourism, number of arrivals',
        'category': 'arrivals',
        'unit': 'number'
    },
    'ST.INT.DPRT': {
        'name': 'International tourism, number of departures',
        'category': 'departures',
        'unit': 'number'
    },
    'ST.INT.RCPT.CD': {
        'name': 'International tourism receipts (current US$)',
        'category': 'receipts',
        'unit': 'current US$'
    },
    'ST.INT.RCPT.XP.ZS': {
        'name': 'International tourism receipts (% of total exports)',
        'category': 'receipts',
        'unit': '% of exports'
    },
    'ST.INT.XPND.CD': {
        'name': 'International tourism expenditures (current US$)',
        'category': 'expenditures',
        'unit': 'current US$'
    },
    'ST.INT.XPND.MP.ZS': {
        'name': 'International tourism expenditures (% of total imports)',
        'category': 'expenditures',
        'unit': '% of imports'
    },
    'ST.INT.TRNR.CD': {
        'name': 'International tourism receipts for travel items (current US$)',
        'category': 'receipts',
        'unit': 'current US$'
    },
    'ST.INT.TRNX.CD': {
        'name': 'International tourism expenditures for travel items (current US$)',
        'category': 'expenditures',
        'unit': 'current US$'
    },
    'ST.INT.TVLR.CD': {
        'name': 'International tourism receipts for passenger transport items',
        'category': 'receipts',
        'unit': 'current US$'
    },
    'ST.INT.TVLX.CD': {
        'name': 'International tourism expenditures for passenger transport items',
        'category': 'expenditures',
        'unit': 'current US$'
    },
}

# All countries for comprehensive tourism data
COUNTRIES = [
    # Top Tourism Destinations (by arrivals)
    'FRA', 'ESP', 'USA', 'CHN', 'ITA', 'TUR', 'MEX', 'DEU', 'THA', 'GBR',
    'JPN', 'AUT', 'GRC', 'HKG', 'MYS', 'RUS', 'PRT', 'CAN', 'POL', 'NLD',
    'ARE', 'HUN', 'MAC', 'IND', 'SAU', 'HRV', 'SGP', 'CZE', 'MAR', 'IDN',

    # Americas
    'BRA', 'ARG', 'CHL', 'COL', 'PER', 'CRI', 'DOM', 'CUB', 'PAN', 'URY',
    'ECU', 'GTM', 'PRY', 'JAM', 'BOL', 'VEN',

    # Europe
    'BEL', 'SWE', 'CHE', 'NOR', 'DNK', 'FIN', 'IRL', 'ROU', 'BGR', 'UKR',
    'SRB', 'SVN', 'SVK', 'LTU', 'LVA', 'EST', 'LUX', 'MLT', 'CYP', 'ISL',

    # Asia Pacific
    'KOR', 'VNM', 'PHL', 'TWN', 'AUS', 'NZL', 'PAK', 'BGD', 'LKA', 'NPL',
    'MMR', 'KHM', 'LAO', 'MNG', 'FJI', 'MDV',

    # Middle East & Africa
    'EGY', 'ZAF', 'ISR', 'JOR', 'LBN', 'QAT', 'KWT', 'BHR', 'OMN', 'TUN',
    'KEN', 'TZA', 'ETH', 'NGA', 'GHA', 'MUS', 'SYC', 'BWA', 'NAM', 'SEN',
]


def fetch_tourism_data(indicator_code: str) -> List[Dict]:
    """Fetch tourism data from World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ';'.join(COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {
        'format': 'json',
        'per_page': 10000,
        'date': '2000:2024',
        'source': 2
    }

    try:
        response = requests.get(url, params=params, timeout=90)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def save_to_database(conn, records: List[Dict], indicator_code: str, indicator_info: Dict) -> int:
    """Save tourism data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.world_tourism_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 2),
            unit VARCHAR(50),
            source VARCHAR(50) DEFAULT 'World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tourism_indicator_year
        ON sofia.world_tourism_data(indicator_code, year DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tourism_country
        ON sofia.world_tourism_data(country_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tourism_category
        ON sofia.world_tourism_data(category)
    """)

    inserted = 0

    for record in records:
        value = record.get('value')
        if value is None:
            continue

        try:
            country_code = record.get('countryiso3code', record.get('country', {}).get('id'))
            country_name = record.get('country', {}).get('value')

            # Normalize country to get country_id
            location = normalize_location(conn, {'country': country_code or country_name})
            country_id = location['country_id']

            cursor.execute("""
                INSERT INTO sofia.world_tourism_data
                (indicator_code, indicator_name, category, country_code, country_name, country_id, year, value, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, year)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """, (
                indicator_code,
                indicator_info.get('name', ''),
                indicator_info.get('category', 'other'),
                country_code,
                country_name,
                country_id,
                int(record.get('date')) if record.get('date') else None,
                float(value),
                indicator_info.get('unit', '')
            ))
            inserted += 1
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def fetch_regional_aggregates() -> List[Dict]:
    """Fetch regional tourism aggregates"""

    regions = ['WLD', 'EAS', 'ECS', 'LCN', 'MEA', 'NAC', 'SAS', 'SSF']
    records = []

    for indicator_code in ['ST.INT.ARVL', 'ST.INT.RCPT.CD']:
        base_url = "https://api.worldbank.org/v2"
        region_str = ';'.join(regions)

        url = f"{base_url}/country/{region_str}/indicator/{indicator_code}"
        params = {
            'format': 'json',
            'per_page': 500,
            'date': '2000:2024'
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if len(data) >= 2 and data[1]:
                    for r in data[1]:
                        r['indicator_code'] = indicator_code
                        records.append(r)
        except:
            continue

    return records


def main():
    print("=" * 80)
    print("WORLD TOURISM DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: World Bank / UNWTO")
    print(f"API: https://api.worldbank.org/v2/")
    print("")
    print(f"Indicators: {len(TOURISM_INDICATORS)}")
    print(f"Countries: {len(COUNTRIES)}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    total_records = 0
    successful = 0
    failed = 0

    # Fetch by category
    categories = {}
    for code, info in TOURISM_INDICATORS.items():
        cat = info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((code, info))

    for cat_name, indicators in categories.items():
        print(f"--- {cat_name.upper()} ---")
        for indicator_code, indicator_info in indicators:
            print(f"  {indicator_info['name'][:55]}...")

            records = fetch_tourism_data(indicator_code)

            if records:
                print(f"    Fetched: {len(records)} records")
                inserted = save_to_database(conn, records, indicator_code, indicator_info)
                total_records += inserted
                successful += 1
                print(f"    Saved: {inserted} records")
            else:
                failed += 1
                print(f"    No data")
        print("")

    # Regional aggregates
    print("--- REGIONAL AGGREGATES ---")
    print("  Fetching regional totals...")
    regional = fetch_regional_aggregates()
    if regional:
        cursor = conn.cursor()
        for r in regional:
            if r.get('value') is None:
                continue
            try:
                country_code = r.get('countryiso3code', r.get('country', {}).get('id', ''))
                country_name = r.get('country', {}).get('value', '')

                # Normalize country to get country_id
                location = normalize_location(conn, {'country': country_code or country_name})
                country_id = location['country_id']

                cursor.execute("""
                    INSERT INTO sofia.world_tourism_data
                    (indicator_code, indicator_name, category, country_code, country_name, country_id, year, value, unit)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator_code, country_code, year)
                    DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
                """, (
                    r.get('indicator_code', ''),
                    r.get('indicator', {}).get('value', ''),
                    'regional',
                    country_code,
                    country_name,
                    country_id,
                    int(r.get('date')) if r.get('date') else None,
                    float(r.get('value')),
                    ''
                ))
                total_records += 1
            except:
                continue
        conn.commit()
        cursor.close()
        print(f"    Saved regional aggregates")
    print("")

    conn.close()

    print("=" * 80)
    print("WORLD TOURISM DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful indicators: {successful}")
    print(f"Failed indicators: {failed}")
    print("")
    print("Categories covered:")
    print("  - International Arrivals (tourists entering)")
    print("  - International Departures (tourists leaving)")
    print("  - Tourism Receipts (money earned from tourism)")
    print("  - Tourism Expenditures (money spent by tourists)")
    print("  - Travel Items (transport, accommodation)")
    print("  - Regional Aggregates (world regions)")
    print("")
    print("Top tourism countries included:")
    print("  France, Spain, USA, China, Italy, Turkey, Mexico")
    print("  Germany, Thailand, UK, Japan, Austria, Greece")
    print("  Brazil, Argentina, UAE, Singapore, India")


if __name__ == '__main__':
    main()
