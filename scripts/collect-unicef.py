#!/usr/bin/env python3

"""
UNICEF Data Collector
Coleta dados de crianças: educação, saúde, nutrição, proteção

API: https://data.unicef.org/open-data/
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

# UNICEF Indicators (via World Bank API which includes UNICEF data)
UNICEF_INDICATORS = {
    # Child mortality
    "SH.DYN.MORT": "Mortality rate, under-5 (per 1,000)",
    "SH.DYN.NMRT": "Mortality rate, neonatal (per 1,000)",
    "SP.DYN.IMRT.IN": "Mortality rate, infant (per 1,000)",
    # Child health
    "SH.IMM.MEAS": "Immunization, measles (% children 12-23 months)",
    "SH.IMM.IDPT": "Immunization, DPT (% children 12-23 months)",
    "SH.STA.STNT.ZS": "Prevalence of stunting, children under 5 (%)",
    "SH.STA.WAST.ZS": "Prevalence of wasting, children under 5 (%)",
    "SH.STA.MALN.ZS": "Prevalence of underweight, children under 5 (%)",
    # Education
    "SE.PRM.NENR": "Primary school enrollment, net (%)",
    "SE.SEC.NENR": "Secondary school enrollment, net (%)",
    "SE.PRM.CMPT.ZS": "Primary completion rate (%)",
    "SE.SEC.CMPT.LO.ZS": "Lower secondary completion rate (%)",
    "SE.ADT.1524.LT.ZS": "Youth literacy rate (15-24)",
    # Child protection
    "SP.M18.2024.FE.ZS": "Women married before age 18 (%)",
    "SH.STA.BRTC.ZS": "Births attended by skilled health staff (%)",
    # Water and sanitation
    "SH.H2O.SMDW.ZS": "Access to safely managed drinking water (%)",
    "SH.STA.SMSS.ZS": "Access to safely managed sanitation (%)",
    # Birth registration
    "SP.REG.BRTH.ZS": "Completeness of birth registration (%)",
}

COUNTRIES = [
    "BRA",
    "USA",
    "CHN",
    "IND",
    "NGA",
    "PAK",
    "IDN",
    "BGD",
    "ETH",
    "COD",
    "MEX",
    "PHL",
    "EGY",
    "VNM",
    "TUR",
    "IRN",
    "THA",
    "ZAF",
    "COL",
    "ARG",
]


def fetch_unicef_data(indicator_code: str) -> List[Dict]:
    """Fetch UNICEF data via World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ";".join(COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 1000, "date": "2010:2024", "source": 2}

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
    """Save UNICEF data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.unicef_children_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(50) DEFAULT 'UNICEF/World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_unicef_indicator_year
        ON sofia.unicef_children_data(indicator_code, year DESC)
    """
    )

    inserted = 0

    for record in records:
        if record.get("value") is None:
            continue

        try:
            cursor.execute(
                """
                INSERT INTO sofia.unicef_children_data
                (indicator_code, indicator_name, country_code, country_name, year, value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, year)
                DO UPDATE SET value = EXCLUDED.value
            """,
                (
                    indicator_code,
                    indicator_name,
                    record.get("countryiso3code", record.get("country", {}).get("id")),
                    record.get("country", {}).get("value"),
                    int(record.get("date")) if record.get("date") else None,
                    float(record.get("value")),
                ),
            )
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("📊 UNICEF - Children's Data (via World Bank)")
    print("=" * 80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://data.unicef.org/")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print(f"📊 Fetching {len(UNICEF_INDICATORS)} children indicators...")
    print("")

    for indicator_code, indicator_name in UNICEF_INDICATORS.items():
        print(f"📈 {indicator_name[:50]}...")

        records = fetch_unicef_data(indicator_code)

        if records:
            print(f"   ✅ Fetched: {len(records)} records")
            inserted = save_to_database(conn, records, indicator_code, indicator_name)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data")

        print("")

    conn.close()

    print("=" * 80)
    print("✅ UNICEF COLLECTION COMPLETE")
    print("=" * 80)
    print(f"💾 Total records: {total_records}")
    print("")
    print("💡 Topics covered:")
    print("  • Child mortality")
    print("  • Immunization")
    print("  • Nutrition (stunting, wasting)")
    print("  • Education enrollment")
    print("  • Water and sanitation")


if __name__ == "__main__":
    main()
