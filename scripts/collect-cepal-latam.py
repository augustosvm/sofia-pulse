#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
CEPAL/ECLAC (Economic Commission for Latin America) Data Collector
Coleta dados da América Latina: feminicídio, economia, desenvolvimento

API: https://statistics.cepal.org/
Portal: https://oig.cepal.org/ (Gender Observatory)
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

import psycopg2
import requests

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost")),
    "port": int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432"))),
    "user": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "sofia")),
    "password": os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "")),
    "database": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "sofia_db")),
}

# CEPAL indicators (via World Bank API for Latin America)
CEPAL_INDICATORS = {
    # Economic
    "NY.GDP.MKTP.CD": "GDP (current US$)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "BN.CAB.XOKA.CD": "Current account balance",
    # Poverty and inequality
    "SI.POV.DDAY": "Poverty headcount ratio at $2.15/day (%)",
    "SI.POV.NAHC": "Poverty headcount ratio at national poverty lines (%)",
    "SI.POV.GINI": "Gini index",
    "SI.DST.10TH.10": "Income share held by highest 10%",
    "SI.DST.FRST.10": "Income share held by lowest 10%",
    # Gender (OIG indicators)
    "SL.TLF.CACT.FE.ZS": "Labor force participation, female (%)",
    "SG.GEN.PARL.ZS": "Women in parliament (%)",
    "SE.ENR.TERT.FM.ZS": "School enrollment tertiary, gender parity",
    # Social
    "SP.DYN.LE00.IN": "Life expectancy at birth",
    "SH.DYN.MORT": "Mortality rate, under-5",
    "SE.ADT.LITR.ZS": "Literacy rate, adult total",
    "SL.UEM.TOTL.ZS": "Unemployment, total (%)",
    # Environment
    "EN.ATM.CO2E.PC": "CO2 emissions (metric tons per capita)",
    "EG.USE.PCAP.KG.OE": "Energy use (kg of oil equivalent per capita)",
}

# Latin America and Caribbean countries
LAC_COUNTRIES = [
    "ARG",
    "BOL",
    "BRA",
    "CHL",
    "COL",
    "CRI",
    "CUB",
    "DOM",
    "ECU",
    "SLV",
    "GTM",
    "HTI",
    "HND",
    "MEX",
    "NIC",
    "PAN",
    "PRY",
    "PER",
    "URY",
    "VEN",
    "JAM",
    "TTO",
    "BHS",
    "BRB",
    "GUY",
    "SUR",
    "BLZ",
]

# Femicide data (hardcoded from CEPAL OIG reports - updated annually)
# Source: https://oig.cepal.org/en/indicators/femicide-or-feminicide
FEMICIDE_DATA = [
    # Country, Year, Femicides, Rate per 100k women
    ("ARG", 2022, 252, 1.1),
    ("BOL", 2022, 113, 1.9),
    ("BRA", 2022, 1437, 1.3),
    ("CHL", 2022, 43, 0.4),
    ("COL", 2022, 614, 2.3),
    ("CRI", 2022, 17, 0.7),
    ("CUB", 2022, 18, 0.3),
    ("DOM", 2022, 117, 2.1),
    ("ECU", 2022, 332, 3.6),
    ("SLV", 2022, 52, 1.5),
    ("GTM", 2022, 235, 2.6),
    ("HND", 2022, 316, 6.0),
    ("MEX", 2022, 968, 1.4),
    ("NIC", 2022, 58, 1.7),
    ("PAN", 2022, 18, 0.8),
    ("PRY", 2022, 45, 1.2),
    ("PER", 2022, 137, 0.8),
    ("URY", 2022, 26, 1.4),
    ("VEN", 2022, None, None),  # No official data
]


def fetch_cepal_data(indicator_code: str) -> List[Dict]:
    """Fetch CEPAL region data via World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ";".join(LAC_COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 1500, "date": "2015:2024", "source": 2}

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


def save_indicators_to_database(conn, records: List[Dict], indicator_code: str, indicator_name: str) -> int:
    """Save CEPAL indicators to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.cepal_latam_data (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(50) DEFAULT 'CEPAL/World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cepal_indicator_year
        ON sofia.cepal_latam_data(indicator_code, year DESC)
    """
    )

    inserted = 0

    for record in records:
        if record.get("value") is None:
            continue

        try:
            # Normalize country
            location = normalize_location(conn, {"country": record.get("country_name") or record.get("country_code")})
            country_id = location["country_id"]

            cursor.execute(
                """
                INSERT INTO sofia.cepal_latam_data
                (indicator_code, indicator_name, country_code, country_name, year, value, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, year)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """,
                (
                    indicator_code,
                    indicator_name,
                    record.get("countryiso3code", record.get("country", {}).get("id")),
                    record.get("country", {}).get("value"),
                    int(record.get("date")) if record.get("date") else None,
                    float(record.get("value")),
                    country_id,
                ),
            )
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def save_femicide_data(conn) -> int:
    """Save CEPAL OIG femicide data"""

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.cepal_femicide (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            country_code VARCHAR(3) NOT NULL,
            year INTEGER NOT NULL,
            femicide_count INTEGER,
            rate_per_100k DECIMAL(10, 2),
            source VARCHAR(100) DEFAULT 'CEPAL OIG',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, year)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_femicide_country_year
        ON sofia.cepal_femicide(country_code, year DESC)
    """
    )

    inserted = 0

    for country, year, count, rate in FEMICIDE_DATA:
        if count is None:
            continue

        try:
            cursor.execute(
                """
                INSERT INTO sofia.cepal_femicide
                (country_code, year, femicide_count, rate_per_100k)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (country_code, year)
                DO UPDATE SET femicide_count = EXCLUDED.femicide_count,
                              rate_per_100k = EXCLUDED.rate_per_100k
            """,
                (country, year, count, rate),
            )
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("📊 CEPAL/ECLAC - Latin America & Caribbean Data")
    print("=" * 80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Sources:")
    print(f"   • https://statistics.cepal.org/")
    print(f"   • https://oig.cepal.org/ (Gender Observatory)")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    # Save femicide data
    print("📈 Femicide data (CEPAL OIG)...")
    femicide_inserted = save_femicide_data(conn)
    total_records += femicide_inserted
    print(f"   💾 Saved: {femicide_inserted} records")
    print("")

    print(f"📊 Fetching {len(CEPAL_INDICATORS)} LAC indicators...")
    print(f"🌎 Countries: {len(LAC_COUNTRIES)}")
    print("")

    for indicator_code, indicator_name in CEPAL_INDICATORS.items():
        print(f"📈 {indicator_name[:50]}...")

        records = fetch_cepal_data(indicator_code)

        if records:
            print(f"   ✅ Fetched: {len(records)} records")
            inserted = save_indicators_to_database(conn, records, indicator_code, indicator_name)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data")

        print("")

    conn.close()

    print("=" * 80)
    print("✅ CEPAL/ECLAC COLLECTION COMPLETE")
    print("=" * 80)
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Key data included:")
    print("  • Femicide by country (OIG)")
    print("  • GDP and economic growth")
    print("  • Poverty and inequality (Gini)")
    print("  • Gender indicators")
    print("  • Social development")


if __name__ == "__main__":
    main()
