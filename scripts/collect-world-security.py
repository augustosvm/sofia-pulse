#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
World Security Data Collector
Coleta dados de segurança dos principais paises das Americas, Europa e Asia

Fontes Oficiais:
- World Bank: Intentional homicides, safety indicators
- UNODC: United Nations Office on Drugs and Crime
- WHO: Violence-related mortality
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

# Top countries by region for security data
COUNTRIES = {
    # Americas - Top 10
    'americas': [
        ('USA', 'United States'),
        ('CAN', 'Canada'),
        ('MEX', 'Mexico'),
        ('BRA', 'Brazil'),
        ('ARG', 'Argentina'),
        ('COL', 'Colombia'),
        ('CHL', 'Chile'),
        ('PER', 'Peru'),
        ('VEN', 'Venezuela'),
        ('ECU', 'Ecuador'),
    ],

    # Europe - Top 10
    'europe': [
        ('DEU', 'Germany'),
        ('GBR', 'United Kingdom'),
        ('FRA', 'France'),
        ('ITA', 'Italy'),
        ('ESP', 'Spain'),
        ('POL', 'Poland'),
        ('NLD', 'Netherlands'),
        ('BEL', 'Belgium'),
        ('SWE', 'Sweden'),
        ('PRT', 'Portugal'),
    ],

    # Asia - Top 10
    'asia': [
        ('CHN', 'China'),
        ('JPN', 'Japan'),
        ('IND', 'India'),
        ('KOR', 'South Korea'),
        ('IDN', 'Indonesia'),
        ('THA', 'Thailand'),
        ('VNM', 'Vietnam'),
        ('MYS', 'Malaysia'),
        ('SGP', 'Singapore'),
        ('PHL', 'Philippines'),
    ],
}

# World Bank Security/Crime Indicators
SECURITY_INDICATORS = {
    # ===========================================
    # HOMICIDES & VIOLENCE
    # ===========================================
    'VC.IHR.PSRC.P5': {
        'name': 'Intentional homicides (per 100,000 people)',
        'category': 'homicide',
        'description': 'Number of unlawful homicides purposely inflicted'
    },
    'VC.IHR.PSRC.FE.P5': {
        'name': 'Intentional homicides, female (per 100,000 female)',
        'category': 'homicide',
        'description': 'Female homicide rate'
    },
    'VC.IHR.PSRC.MA.P5': {
        'name': 'Intentional homicides, male (per 100,000 male)',
        'category': 'homicide',
        'description': 'Male homicide rate'
    },

    # ===========================================
    # SAFETY PERCEPTION
    # ===========================================
    # Note: Limited availability, using proxy indicators

    # ===========================================
    # PRISON & JUSTICE
    # ===========================================
    'VC.PRS.RDEN': {
        'name': 'Prison population rate (per 100,000)',
        'category': 'justice',
        'description': 'Incarceration rate'
    },

    # ===========================================
    # MORTALITY (Violence-related)
    # ===========================================
    'SH.DTH.INJR.ZS': {
        'name': 'Mortality from injuries (% of total)',
        'category': 'mortality',
        'description': 'Deaths from injuries including violence'
    },
    'SH.STA.TRAF.P5': {
        'name': 'Mortality from road traffic (per 100,000)',
        'category': 'accidents',
        'description': 'Road traffic death rate'
    },

    # ===========================================
    # MILITARY & CONFLICT
    # ===========================================
    'MS.MIL.XPND.GD.ZS': {
        'name': 'Military expenditure (% of GDP)',
        'category': 'military',
        'description': 'Defense spending as % of GDP'
    },
    'MS.MIL.TOTL.P1': {
        'name': 'Armed forces personnel, total',
        'category': 'military',
        'description': 'Total military personnel'
    },

    # ===========================================
    # REFUGEES & DISPLACEMENT
    # ===========================================
    'SM.POP.REFG': {
        'name': 'Refugee population by country of origin',
        'category': 'displacement',
        'description': 'Refugees originating from country'
    },
    'SM.POP.REFG.OR': {
        'name': 'Refugee population by country of asylum',
        'category': 'displacement',
        'description': 'Refugees hosted by country'
    },

    # ===========================================
    # GOVERNANCE & RULE OF LAW
    # ===========================================
    'CC.EST': {
        'name': 'Control of Corruption: Estimate',
        'category': 'governance',
        'description': 'Corruption perception index'
    },
    'RL.EST': {
        'name': 'Rule of Law: Estimate',
        'category': 'governance',
        'description': 'Rule of law index'
    },
    'PV.EST': {
        'name': 'Political Stability: Estimate',
        'category': 'governance',
        'description': 'Political stability and absence of violence'
    },
}


def fetch_security_data(indicator_code: str, countries: List[str]) -> List[Dict]:
    """Fetch security data from World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ';'.join(countries)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {
        'format': 'json',
        'per_page': 2000,
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
        print(f"    Error: {str(e)[:80]}")
        return []


def save_to_database(conn, records: List[Dict], indicator_code: str, indicator_info: Dict, region: str) -> int:
    """Save world security data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.world_security_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            region VARCHAR(20),
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(50) DEFAULT 'World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_world_security_region
        ON sofia.world_security_data(region, country_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_world_security_indicator
        ON sofia.world_security_data(indicator_code, year DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_world_security_category
        ON sofia.world_security_data(category)
    """)

    inserted = 0

    for record in records:
        value = record.get('value')
        if value is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.world_security_data
                (indicator_code, indicator_name, category, region, country_code, country_name, year, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, year)
                DO UPDATE SET value = EXCLUDED.value, region = EXCLUDED.region
            """, (
                indicator_code,
                indicator_info.get('name', ''),
                indicator_info.get('category', 'other'),
                region,
                record.get('countryiso3code', record.get('country', {}).get('id')),
                record.get('country', {}).get('value'),
                int(record.get('date')) if record.get('date') else None,
                float(value)
            ))
            inserted += 1
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("WORLD SECURITY DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources:")
    print(f"  - World Bank Development Indicators")
    print(f"  - UNODC (via World Bank)")
    print(f"  - WHO (via World Bank)")
    print("")
    print(f"Coverage:")
    print(f"  - Americas: {len(COUNTRIES['americas'])} countries")
    print(f"  - Europe: {len(COUNTRIES['europe'])} countries")
    print(f"  - Asia: {len(COUNTRIES['asia'])} countries")
    print(f"  - Indicators: {len(SECURITY_INDICATORS)}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    # Process by region
    for region_name, country_list in COUNTRIES.items():
        print(f"=== {region_name.upper()} ===")
        print(f"Countries: {', '.join([c[1] for c in country_list])}")
        print("")

        country_codes = [c[0] for c in country_list]

        # Group indicators by category
        categories = {}
        for code, info in SECURITY_INDICATORS.items():
            cat = info['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((code, info))

        for cat_name, indicators in categories.items():
            print(f"--- {cat_name.upper()} ---")
            for indicator_code, indicator_info in indicators:
                print(f"  {indicator_info['name'][:50]}...")

                records = fetch_security_data(indicator_code, country_codes)

                if records:
                    print(f"    Fetched: {len(records)} records")
                    inserted = save_to_database(conn, records, indicator_code, indicator_info, region_name)
                    total_records += inserted
                    print(f"    Saved: {inserted} records")
                else:
                    print(f"    No data")
            print("")

    conn.close()

    print("=" * 80)
    print("WORLD SECURITY DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Regions covered:")
    print("  Americas: USA, Canada, Mexico, Brazil, Argentina, Colombia,")
    print("            Chile, Peru, Venezuela, Ecuador")
    print("")
    print("  Europe: Germany, UK, France, Italy, Spain, Poland,")
    print("          Netherlands, Belgium, Sweden, Portugal")
    print("")
    print("  Asia: China, Japan, India, South Korea, Indonesia,")
    print("        Thailand, Vietnam, Malaysia, Singapore, Philippines")
    print("")
    print("Indicators collected:")
    print("  - Intentional homicides (per 100,000)")
    print("  - Female/Male homicide rates")
    print("  - Prison population rate")
    print("  - Mortality from injuries")
    print("  - Road traffic deaths")
    print("  - Military expenditure")
    print("  - Refugee populations")
    print("  - Corruption control")
    print("  - Rule of law index")
    print("  - Political stability")
    print("")
    print("Table created: sofia.world_security_data")


if __name__ == '__main__':
    main()
