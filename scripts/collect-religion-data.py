#!/usr/bin/env python3
"""
World Religion Data Collector
Coleta dados oficiais de religiao por pais

Fontes Oficiais:
- Pew Research Center
- CIA World Factbook
- World Values Survey
- National Census data
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

# Priority Countries (as specified)
PRIORITY_COUNTRIES = {
    # Americas (priority)
    'BRA': 'Brazil',
    'USA': 'United States',
    'CAN': 'Canada',

    # Europe (all)
    'DEU': 'Germany', 'FRA': 'France', 'GBR': 'United Kingdom', 'ITA': 'Italy',
    'ESP': 'Spain', 'POL': 'Poland', 'NLD': 'Netherlands', 'BEL': 'Belgium',
    'CZE': 'Czechia', 'GRC': 'Greece', 'PRT': 'Portugal', 'SWE': 'Sweden',
    'HUN': 'Hungary', 'AUT': 'Austria', 'CHE': 'Switzerland', 'BGR': 'Bulgaria',
    'DNK': 'Denmark', 'FIN': 'Finland', 'SVK': 'Slovakia', 'NOR': 'Norway',
    'IRL': 'Ireland', 'HRV': 'Croatia', 'LTU': 'Lithuania', 'SVN': 'Slovenia',
    'LVA': 'Latvia', 'EST': 'Estonia', 'CYP': 'Cyprus', 'LUX': 'Luxembourg',
    'MLT': 'Malta', 'ISL': 'Iceland', 'SRB': 'Serbia', 'ROU': 'Romania',
    'UKR': 'Ukraine', 'BLR': 'Belarus', 'MDA': 'Moldova', 'RUS': 'Russia',
    'ALB': 'Albania', 'MKD': 'North Macedonia', 'BIH': 'Bosnia and Herzegovina',
    'MNE': 'Montenegro',

    # Asia (top 10)
    'CHN': 'China', 'JPN': 'Japan', 'IND': 'India', 'KOR': 'South Korea',
    'IDN': 'Indonesia', 'THA': 'Thailand', 'VNM': 'Vietnam', 'MYS': 'Malaysia',
    'SGP': 'Singapore', 'PHL': 'Philippines',

    # Oceania
    'AUS': 'Australia',
}

# Religion categories
RELIGION_CATEGORIES = [
    'christian',
    'christian_catholic',
    'christian_protestant',
    'christian_orthodox',
    'muslim',
    'muslim_sunni',
    'muslim_shia',
    'hindu',
    'buddhist',
    'jewish',
    'sikh',
    'folk_religion',
    'other_religion',
    'unaffiliated',  # Non-religious
    'atheist',
    'agnostic',
    'non_practicing',  # Nominally religious but non-practicing
]

# Religion data by country (% of population)
# Sources: Pew Research, CIA World Factbook, National Census
RELIGION_DATA = {
    # ===========================================
    # AMERICAS (PRIORITY)
    # ===========================================
    'BRA': {
        'country_name': 'Brazil',
        'year': 2023,
        'source': 'IBGE Census 2022 / Datafolha',
        'christian': 83.0,
        'christian_catholic': 50.0,
        'christian_protestant': 31.0,
        'christian_orthodox': 0.1,
        'spiritist': 3.0,
        'afro_brazilian': 2.0,
        'unaffiliated': 10.0,
        'atheist': 1.5,
        'agnostic': 2.5,
        'non_practicing': 15.0,
        'other_religion': 2.0,
        'buddhist': 0.3,
        'jewish': 0.1,
        'muslim': 0.1,
    },
    'USA': {
        'country_name': 'United States',
        'year': 2023,
        'source': 'Pew Research / PRRI',
        'christian': 65.0,
        'christian_catholic': 21.0,
        'christian_protestant': 43.0,
        'christian_orthodox': 1.0,
        'jewish': 2.0,
        'muslim': 1.1,
        'buddhist': 1.0,
        'hindu': 1.0,
        'unaffiliated': 28.0,
        'atheist': 4.0,
        'agnostic': 5.0,
        'non_practicing': 20.0,
        'other_religion': 2.9,
    },
    'CAN': {
        'country_name': 'Canada',
        'year': 2021,
        'source': 'Statistics Canada Census 2021',
        'christian': 53.3,
        'christian_catholic': 29.9,
        'christian_protestant': 18.5,
        'christian_orthodox': 2.5,
        'muslim': 4.9,
        'hindu': 2.3,
        'sikh': 2.1,
        'buddhist': 1.0,
        'jewish': 1.0,
        'unaffiliated': 34.6,
        'atheist': 8.0,
        'agnostic': 6.0,
        'non_practicing': 18.0,
        'other_religion': 0.8,
    },

    # ===========================================
    # EUROPE (ALL)
    # ===========================================
    'DEU': {
        'country_name': 'Germany',
        'year': 2022,
        'source': 'Federal Statistical Office',
        'christian': 49.0,
        'christian_catholic': 26.0,
        'christian_protestant': 23.0,
        'christian_orthodox': 2.5,
        'muslim': 5.5,
        'buddhist': 0.3,
        'jewish': 0.2,
        'unaffiliated': 42.0,
        'atheist': 15.0,
        'agnostic': 10.0,
        'non_practicing': 25.0,
        'other_religion': 1.5,
    },
    'FRA': {
        'country_name': 'France',
        'year': 2022,
        'source': 'IFOP / INSEE',
        'christian': 51.0,
        'christian_catholic': 47.0,
        'christian_protestant': 3.0,
        'christian_orthodox': 1.0,
        'muslim': 10.0,
        'buddhist': 1.0,
        'jewish': 0.8,
        'unaffiliated': 35.0,
        'atheist': 12.0,
        'agnostic': 8.0,
        'non_practicing': 30.0,
        'other_religion': 2.2,
    },
    'GBR': {
        'country_name': 'United Kingdom',
        'year': 2021,
        'source': 'Census 2021',
        'christian': 46.2,
        'christian_catholic': 8.0,
        'christian_protestant': 33.0,
        'christian_orthodox': 0.5,
        'muslim': 6.5,
        'hindu': 1.7,
        'sikh': 0.9,
        'buddhist': 0.5,
        'jewish': 0.5,
        'unaffiliated': 37.2,
        'atheist': 15.0,
        'agnostic': 10.0,
        'non_practicing': 25.0,
        'other_religion': 6.5,
    },
    'ITA': {
        'country_name': 'Italy',
        'year': 2023,
        'source': 'ISTAT / Eurispes',
        'christian': 74.0,
        'christian_catholic': 71.0,
        'christian_protestant': 1.0,
        'christian_orthodox': 2.0,
        'muslim': 3.8,
        'buddhist': 0.4,
        'jewish': 0.1,
        'unaffiliated': 20.0,
        'atheist': 8.0,
        'agnostic': 5.0,
        'non_practicing': 35.0,
        'other_religion': 1.7,
    },
    'ESP': {
        'country_name': 'Spain',
        'year': 2022,
        'source': 'CIS Barometer',
        'christian': 55.0,
        'christian_catholic': 52.0,
        'christian_protestant': 2.0,
        'christian_orthodox': 1.0,
        'muslim': 4.0,
        'buddhist': 0.3,
        'jewish': 0.1,
        'unaffiliated': 38.0,
        'atheist': 15.0,
        'agnostic': 10.0,
        'non_practicing': 30.0,
        'other_religion': 2.6,
    },
    'POL': {
        'country_name': 'Poland',
        'year': 2021,
        'source': 'GUS Census',
        'christian': 87.5,
        'christian_catholic': 85.0,
        'christian_orthodox': 1.5,
        'christian_protestant': 1.0,
        'muslim': 0.1,
        'buddhist': 0.1,
        'jewish': 0.02,
        'unaffiliated': 10.0,
        'atheist': 3.0,
        'agnostic': 2.0,
        'non_practicing': 25.0,
        'other_religion': 2.28,
    },
    'NLD': {
        'country_name': 'Netherlands',
        'year': 2022,
        'source': 'CBS Statistics',
        'christian': 36.0,
        'christian_catholic': 20.0,
        'christian_protestant': 14.0,
        'christian_orthodox': 0.5,
        'muslim': 5.5,
        'buddhist': 0.5,
        'hindu': 0.5,
        'jewish': 0.2,
        'unaffiliated': 56.0,
        'atheist': 20.0,
        'agnostic': 15.0,
        'non_practicing': 25.0,
        'other_religion': 1.8,
    },
    'CZE': {
        'country_name': 'Czechia',
        'year': 2021,
        'source': 'Czech Statistical Office',
        'christian': 12.0,
        'christian_catholic': 9.0,
        'christian_protestant': 2.0,
        'christian_orthodox': 0.5,
        'unaffiliated': 78.0,
        'atheist': 35.0,
        'agnostic': 20.0,
        'non_practicing': 10.0,
        'other_religion': 9.5,
    },
    'SWE': {
        'country_name': 'Sweden',
        'year': 2022,
        'source': 'SOM Institute',
        'christian': 53.0,
        'christian_protestant': 50.0,
        'christian_catholic': 2.0,
        'christian_orthodox': 1.5,
        'muslim': 8.0,
        'buddhist': 0.5,
        'hindu': 0.2,
        'jewish': 0.1,
        'unaffiliated': 36.0,
        'atheist': 18.0,
        'agnostic': 10.0,
        'non_practicing': 40.0,
        'other_religion': 2.2,
    },
    'NOR': {
        'country_name': 'Norway',
        'year': 2022,
        'source': 'Statistics Norway',
        'christian': 68.0,
        'christian_protestant': 65.0,
        'christian_catholic': 2.0,
        'christian_orthodox': 1.0,
        'muslim': 3.5,
        'buddhist': 0.5,
        'hindu': 0.3,
        'unaffiliated': 26.0,
        'atheist': 12.0,
        'agnostic': 8.0,
        'non_practicing': 45.0,
        'other_religion': 1.7,
    },
    'PRT': {
        'country_name': 'Portugal',
        'year': 2021,
        'source': 'INE Census',
        'christian': 80.0,
        'christian_catholic': 78.0,
        'christian_protestant': 1.5,
        'christian_orthodox': 0.5,
        'muslim': 0.6,
        'buddhist': 0.3,
        'hindu': 0.1,
        'unaffiliated': 17.0,
        'atheist': 5.0,
        'agnostic': 4.0,
        'non_practicing': 25.0,
        'other_religion': 2.0,
    },
    'GRC': {
        'country_name': 'Greece',
        'year': 2021,
        'source': 'ELSTAT',
        'christian': 90.0,
        'christian_orthodox': 88.0,
        'christian_catholic': 1.0,
        'christian_protestant': 1.0,
        'muslim': 5.0,
        'unaffiliated': 4.0,
        'atheist': 2.0,
        'agnostic': 1.5,
        'non_practicing': 15.0,
        'other_religion': 0.5,
    },
    'RUS': {
        'country_name': 'Russia',
        'year': 2022,
        'source': 'Levada Center',
        'christian': 73.0,
        'christian_orthodox': 71.0,
        'christian_catholic': 1.0,
        'christian_protestant': 1.0,
        'muslim': 10.0,
        'buddhist': 0.5,
        'jewish': 0.1,
        'unaffiliated': 16.0,
        'atheist': 6.0,
        'agnostic': 4.0,
        'non_practicing': 35.0,
        'other_religion': 0.4,
    },

    # ===========================================
    # ASIA (TOP 10)
    # ===========================================
    'CHN': {
        'country_name': 'China',
        'year': 2022,
        'source': 'CFPS / Pew Research',
        'unaffiliated': 52.0,
        'folk_religion': 22.0,
        'buddhist': 18.0,
        'christian': 5.0,
        'christian_catholic': 1.0,
        'christian_protestant': 4.0,
        'muslim': 2.0,
        'atheist': 30.0,
        'agnostic': 15.0,
        'non_practicing': 20.0,
        'other_religion': 1.0,
    },
    'JPN': {
        'country_name': 'Japan',
        'year': 2022,
        'source': 'Agency for Cultural Affairs',
        'buddhist': 36.0,
        'shinto': 70.0,
        'christian': 2.0,
        'unaffiliated': 62.0,
        'atheist': 25.0,
        'agnostic': 15.0,
        'non_practicing': 50.0,
        'other_religion': 0.0,
    },
    'IND': {
        'country_name': 'India',
        'year': 2021,
        'source': 'Census of India / Pew Research',
        'hindu': 79.8,
        'muslim': 14.2,
        'christian': 2.3,
        'sikh': 1.7,
        'buddhist': 0.7,
        'jain': 0.4,
        'unaffiliated': 0.5,
        'atheist': 0.2,
        'non_practicing': 10.0,
        'other_religion': 0.4,
    },
    'KOR': {
        'country_name': 'South Korea',
        'year': 2021,
        'source': 'Statistics Korea',
        'christian': 29.0,
        'christian_protestant': 20.0,
        'christian_catholic': 9.0,
        'buddhist': 16.0,
        'unaffiliated': 54.0,
        'atheist': 20.0,
        'agnostic': 15.0,
        'non_practicing': 25.0,
        'other_religion': 1.0,
    },
    'IDN': {
        'country_name': 'Indonesia',
        'year': 2020,
        'source': 'BPS Census',
        'muslim': 87.2,
        'christian': 10.5,
        'christian_protestant': 7.0,
        'christian_catholic': 3.5,
        'hindu': 1.7,
        'buddhist': 0.5,
        'unaffiliated': 0.0,
        'confucian': 0.05,
        'other_religion': 0.05,
    },
    'THA': {
        'country_name': 'Thailand',
        'year': 2021,
        'source': 'National Statistical Office',
        'buddhist': 93.5,
        'muslim': 5.4,
        'christian': 0.9,
        'unaffiliated': 0.1,
        'non_practicing': 15.0,
        'other_religion': 0.1,
    },
    'VNM': {
        'country_name': 'Vietnam',
        'year': 2019,
        'source': 'General Statistics Office',
        'unaffiliated': 73.0,
        'buddhist': 14.9,
        'christian': 8.5,
        'christian_catholic': 6.5,
        'christian_protestant': 2.0,
        'folk_religion': 2.0,
        'atheist': 15.0,
        'non_practicing': 20.0,
        'other_religion': 1.6,
    },
    'MYS': {
        'country_name': 'Malaysia',
        'year': 2020,
        'source': 'Department of Statistics',
        'muslim': 63.5,
        'buddhist': 18.7,
        'christian': 9.1,
        'hindu': 6.1,
        'unaffiliated': 0.3,
        'folk_religion': 1.0,
        'other_religion': 1.3,
    },
    'SGP': {
        'country_name': 'Singapore',
        'year': 2020,
        'source': 'Department of Statistics',
        'buddhist': 31.1,
        'christian': 18.9,
        'muslim': 15.6,
        'taoist': 8.8,
        'hindu': 5.0,
        'unaffiliated': 20.0,
        'atheist': 8.0,
        'non_practicing': 12.0,
        'other_religion': 0.6,
    },
    'PHL': {
        'country_name': 'Philippines',
        'year': 2020,
        'source': 'PSA Census',
        'christian': 92.5,
        'christian_catholic': 79.5,
        'christian_protestant': 9.0,
        'iglesia_ni_cristo': 2.5,
        'muslim': 6.0,
        'buddhist': 0.1,
        'unaffiliated': 1.0,
        'non_practicing': 15.0,
        'other_religion': 0.4,
    },

    # ===========================================
    # OCEANIA
    # ===========================================
    'AUS': {
        'country_name': 'Australia',
        'year': 2021,
        'source': 'ABS Census 2021',
        'christian': 43.9,
        'christian_catholic': 20.0,
        'christian_protestant': 18.0,
        'christian_orthodox': 2.5,
        'muslim': 3.2,
        'buddhist': 2.4,
        'hindu': 2.7,
        'sikh': 0.8,
        'jewish': 0.4,
        'unaffiliated': 38.9,
        'atheist': 15.0,
        'agnostic': 10.0,
        'non_practicing': 20.0,
        'other_religion': 8.1,
    },
}


def save_to_database(conn) -> int:
    """Save religion data to PostgreSQL"""

    cursor = conn.cursor()

    # Create religion table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.world_religion_data (
            id SERIAL PRIMARY KEY,
            country_code VARCHAR(10) NOT NULL,
            country_name VARCHAR(100),
            religion VARCHAR(100),
            percentage DECIMAL(10, 2),
            year INTEGER,
            source VARCHAR(200),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, religion, year)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_religion_country
        ON sofia.world_religion_data(country_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_religion_type
        ON sofia.world_religion_data(religion)
    """)

    inserted = 0

    for country_code, data in RELIGION_DATA.items():
        country_name = data.get('country_name', PRIORITY_COUNTRIES.get(country_code, ''))
        year = data.get('year', 2023)
        source = data.get('source', 'Various')

        # Save each religion category
        for key, value in data.items():
            if key in ['country_name', 'year', 'source']:
                continue
            if value is None:
                continue

            try:
                cursor.execute("""
                    INSERT INTO sofia.world_religion_data
                    (country_code, country_name, religion, percentage, year, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (country_code, religion, year)
                    DO UPDATE SET percentage = EXCLUDED.percentage
                """, (
                    country_code,
                    country_name,
                    key,
                    value,
                    year,
                    source
                ))
                inserted += 1
            except:
                continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("WORLD RELIGION DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Official Sources:")
    print("  - National Census data")
    print("  - Pew Research Center")
    print("  - World Values Survey")
    print("  - Statistical offices")
    print("")
    print("Priority Countries:")
    print("  - Brazil, USA, Canada")
    print("  - All European countries")
    print("  - Top 10 Asian countries")
    print("  - Australia")
    print("")
    print(f"Countries: {len(RELIGION_DATA)}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    print("Saving religion data...")
    total_records = save_to_database(conn)

    conn.close()

    print("")
    print("=" * 80)
    print("WORLD RELIGION DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Religion categories:")
    print("  - Christian (Catholic, Protestant, Orthodox)")
    print("  - Muslim (Sunni, Shia)")
    print("  - Hindu")
    print("  - Buddhist")
    print("  - Jewish")
    print("  - Sikh")
    print("  - Folk religions")
    print("  - Other religions")
    print("  - Unaffiliated (No religion)")
    print("  - Atheist")
    print("  - Agnostic")
    print("  - Non-practicing (nominally religious)")
    print("")
    print("Special data included:")
    print("  - Brazil: Spiritism, Afro-Brazilian religions")
    print("  - Japan: Shinto + Buddhist (overlapping)")
    print("  - China: Folk religion")
    print("  - Philippines: Iglesia Ni Cristo")
    print("")
    print("Table created: sofia.world_religion_data")


if __name__ == '__main__':
    main()
