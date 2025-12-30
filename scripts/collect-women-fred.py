#!/usr/bin/env python3

"""
US Federal Reserve Women's Data Collector - FRED API
Coleta dados de mulheres dos EUA via Federal Reserve Economic Data

API: https://fred.stlouisfed.org/docs/api/fred/
Key: Free registration required at https://fred.stlouisfed.org/docs/api/api_key.html
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

# FRED API Key (free registration)
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# FRED Series for Women's Economic Data
# Reference: https://fred.stlouisfed.org/tags/series?t=women
FRED_WOMEN_SERIES = {
    # ===========================================
    # LABOR FORCE PARTICIPATION
    # ===========================================
    "LNS11300002": {
        "name": "Civilian Labor Force Participation Rate: Women",
        "category": "labor_participation",
        "frequency": "monthly",
    },
    "LNS11300001": {
        "name": "Civilian Labor Force Participation Rate: Men",
        "category": "labor_participation",
        "frequency": "monthly",
    },
    "LNS11300012": {
        "name": "Labor Force Participation Rate: Women, 25-54 yrs",
        "category": "labor_participation",
        "frequency": "monthly",
    },
    "LNS11324230": {
        "name": "Labor Force Participation Rate: Women with children under 18",
        "category": "labor_participation",
        "frequency": "monthly",
    },
    # By Race/Ethnicity
    "LNS11300029": {
        "name": "Labor Force Participation Rate: White Women",
        "category": "labor_by_race",
        "frequency": "monthly",
    },
    "LNS11300032": {
        "name": "Labor Force Participation Rate: Black Women",
        "category": "labor_by_race",
        "frequency": "monthly",
    },
    "LNS11300035": {
        "name": "Labor Force Participation Rate: Hispanic Women",
        "category": "labor_by_race",
        "frequency": "monthly",
    },
    "LNS11332185": {
        "name": "Labor Force Participation Rate: Asian Women",
        "category": "labor_by_race",
        "frequency": "monthly",
    },
    # ===========================================
    # EMPLOYMENT
    # ===========================================
    "LNS12000002": {"name": "Employment Level: Women", "category": "employment", "frequency": "monthly"},
    "LNS12300002": {"name": "Employment-Population Ratio: Women", "category": "employment", "frequency": "monthly"},
    "LNS12032185": {"name": "Employment Level: Asian Women", "category": "employment_by_race", "frequency": "monthly"},
    # ===========================================
    # UNEMPLOYMENT
    # ===========================================
    "LNS14000002": {"name": "Unemployment Rate: Women", "category": "unemployment", "frequency": "monthly"},
    "LNS14000001": {"name": "Unemployment Rate: Men", "category": "unemployment", "frequency": "monthly"},
    "LNS14000029": {
        "name": "Unemployment Rate: White Women",
        "category": "unemployment_by_race",
        "frequency": "monthly",
    },
    "LNS14000032": {
        "name": "Unemployment Rate: Black Women",
        "category": "unemployment_by_race",
        "frequency": "monthly",
    },
    "LNS14000035": {
        "name": "Unemployment Rate: Hispanic Women",
        "category": "unemployment_by_race",
        "frequency": "monthly",
    },
    "LNS14032185": {
        "name": "Unemployment Rate: Asian Women",
        "category": "unemployment_by_race",
        "frequency": "monthly",
    },
    # ===========================================
    # EARNINGS & WAGES
    # ===========================================
    "LEU0252881600A": {
        "name": "Median Usual Weekly Earnings: Women, Full-Time",
        "category": "earnings",
        "frequency": "quarterly",
    },
    "LEU0252881500A": {
        "name": "Median Usual Weekly Earnings: Men, Full-Time",
        "category": "earnings",
        "frequency": "quarterly",
    },
    "LES1252881600Q": {"name": "Median Weekly Earnings: Women, 16+", "category": "earnings", "frequency": "quarterly"},
    # By Education
    "LEU0254537200A": {
        "name": "Median Earnings: Women, High School Graduate",
        "category": "earnings_education",
        "frequency": "quarterly",
    },
    "LEU0254537700A": {
        "name": "Median Earnings: Women, Bachelor Degree+",
        "category": "earnings_education",
        "frequency": "quarterly",
    },
    # ===========================================
    # OCCUPATION DATA
    # ===========================================
    "LEU0254909200Q": {
        "name": "Women in Management, Professional Occupations",
        "category": "occupation",
        "frequency": "quarterly",
    },
    "LEU0254923400Q": {"name": "Women in Service Occupations", "category": "occupation", "frequency": "quarterly"},
    # ===========================================
    # SELF-EMPLOYMENT
    # ===========================================
    "LNS12027716": {
        "name": "Self-Employed Women, Unincorporated",
        "category": "self_employment",
        "frequency": "monthly",
    },
    # ===========================================
    # BUSINESS OWNERSHIP (Census Data via FRED)
    # ===========================================
    "WOMENBUS": {"name": "Women-Owned Business Establishments", "category": "business", "frequency": "annual"},
}


def fetch_fred_series(series_id: str) -> List[Dict]:
    """Fetch data from FRED API"""

    if not FRED_API_KEY:
        print("    Warning: No FRED_API_KEY set, using limited access")
        # Try without API key (very limited)

    base_url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY if FRED_API_KEY else "demo",
        "file_type": "json",
        "observation_start": "2000-01-01",
        "observation_end": "2024-12-31",
    }

    try:
        response = requests.get(base_url, params=params, timeout=60)

        if response.status_code == 400:
            # Try without API key
            params["api_key"] = ""
            response = requests.get(base_url, params=params, timeout=60)

        if response.status_code != 200:
            return []

        data = response.json()

        if "observations" in data:
            return data["observations"]
        return []

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def save_to_database(conn, records: List[Dict], series_id: str, series_info: Dict) -> int:
    """Save FRED women's data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.women_fred_data (
            id SERIAL PRIMARY KEY,
            series_id VARCHAR(50) NOT NULL,
            series_name TEXT,
            category VARCHAR(50),
            date DATE,
            value DECIMAL(18, 6),
            frequency VARCHAR(20),
            country VARCHAR(10) DEFAULT 'USA',
            source VARCHAR(50) DEFAULT 'FRED',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series_id, date)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fred_series_date
        ON sofia.women_fred_data(series_id, date DESC)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fred_category
        ON sofia.women_fred_data(category)
    """
    )

    inserted = 0

    for record in records:
        value = record.get("value", "")
        if value == "." or value == "" or value is None:
            continue

        try:
            cursor.execute(
                """
                INSERT INTO sofia.women_fred_data
                (series_id, series_name, category, date, value, frequency)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_id, date)
                DO UPDATE SET value = EXCLUDED.value
            """,
                (
                    series_id,
                    series_info.get("name", ""),
                    series_info.get("category", "other"),
                    record.get("date"),
                    float(value),
                    series_info.get("frequency", "monthly"),
                ),
            )
            inserted += 1
        except Exception:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("US FEDERAL RESERVE WOMEN'S DATA - FRED")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: Federal Reserve Economic Data (FRED)")
    print(f"API: https://fred.stlouisfed.org/")
    print("")
    print(f"Series: {len(FRED_WOMEN_SERIES)}")
    print(f"API Key: {'Configured' if FRED_API_KEY else 'NOT SET (limited access)'}")
    print("")

    if not FRED_API_KEY:
        print("TIP: Get free API key at https://fred.stlouisfed.org/docs/api/api_key.html")
        print("     Set FRED_API_KEY environment variable")
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

    # Group by category
    categories = {}
    for series_id, info in FRED_WOMEN_SERIES.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((series_id, info))

    for cat_name, series_list in categories.items():
        print(f"--- {cat_name.upper().replace('_', ' ')} ---")
        for series_id, series_info in series_list:
            print(f"  {series_info['name'][:55]}...")

            records = fetch_fred_series(series_id)

            if records:
                print(f"    Fetched: {len(records)} observations")
                inserted = save_to_database(conn, records, series_id, series_info)
                total_records += inserted
                successful += 1
                print(f"    Saved: {inserted} records")
            else:
                failed += 1
                print(f"    No data")
        print("")

    conn.close()

    print("=" * 80)
    print("FRED WOMEN'S DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful series: {successful}")
    print(f"Failed series: {failed}")
    print("")
    print("Categories covered:")
    print("  - Labor Force Participation (overall + by race)")
    print("  - Employment Levels & Ratios")
    print("  - Unemployment Rates (overall + by race)")
    print("  - Earnings & Wages")
    print("  - Occupation Data")
    print("  - Self-Employment")
    print("  - Business Ownership")


if __name__ == "__main__":
    main()
