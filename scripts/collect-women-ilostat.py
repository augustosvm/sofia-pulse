#!/usr/bin/env python3

"""
ILO Women's Labor Data Collector - ILOSTAT
Coleta dados de trabalho feminino de todos os paises via ILO SDMX API

API: https://ilostat.ilo.org/data/
SDMX: https://www.ilo.org/sdmx/ws/rest/
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

# ILO Indicators for Women's Labor Data
# Reference: https://ilostat.ilo.org/data/
ILO_WOMEN_INDICATORS = {
    # ===========================================
    # LABOR FORCE
    # ===========================================
    "EAP_DWAP_SEX_AGE_RT": {
        "name": "Labour force participation rate by sex and age",
        "category": "labor_force",
        "sdmx_flow": "DF_EAP_DWAP_SEX_AGE_RT",
    },
    "EAP_2WAP_SEX_AGE_NB": {
        "name": "Labour force by sex and age (thousands)",
        "category": "labor_force",
        "sdmx_flow": "DF_EAP_2WAP_SEX_AGE_NB",
    },
    # ===========================================
    # EMPLOYMENT
    # ===========================================
    "EMP_DWAP_SEX_AGE_RT": {
        "name": "Employment-to-population ratio by sex and age",
        "category": "employment",
        "sdmx_flow": "DF_EMP_DWAP_SEX_AGE_RT",
    },
    "EMP_2EMP_SEX_ECO_NB": {
        "name": "Employment by sex and economic activity (thousands)",
        "category": "employment",
        "sdmx_flow": "DF_EMP_2EMP_SEX_ECO_NB",
    },
    "EMP_2EMP_SEX_STE_NB": {
        "name": "Employment by sex and status in employment",
        "category": "employment",
        "sdmx_flow": "DF_EMP_2EMP_SEX_STE_NB",
    },
    "EMP_2EMP_SEX_OCU_NB": {
        "name": "Employment by sex and occupation",
        "category": "employment",
        "sdmx_flow": "DF_EMP_2EMP_SEX_OCU_NB",
    },
    # ===========================================
    # UNEMPLOYMENT
    # ===========================================
    "UNE_DEAP_SEX_AGE_RT": {
        "name": "Unemployment rate by sex and age",
        "category": "unemployment",
        "sdmx_flow": "DF_UNE_DEAP_SEX_AGE_RT",
    },
    "UNE_2EAP_SEX_AGE_NB": {
        "name": "Unemployment by sex and age (thousands)",
        "category": "unemployment",
        "sdmx_flow": "DF_UNE_2EAP_SEX_AGE_NB",
    },
    "UNE_TUNE_SEX_AGE_NB": {
        "name": "Youth unemployment by sex",
        "category": "unemployment",
        "sdmx_flow": "DF_UNE_TUNE_SEX_AGE_NB",
    },
    # ===========================================
    # EARNINGS & WAGES
    # ===========================================
    "EAR_4MTH_SEX_ECO_CUR_NB": {
        "name": "Mean nominal monthly earnings by sex and economic activity",
        "category": "earnings",
        "sdmx_flow": "DF_EAR_4MTH_SEX_ECO_CUR_NB",
    },
    "EAR_GGAP_SEX_OCU_RT": {
        "name": "Gender wage gap by occupation",
        "category": "earnings",
        "sdmx_flow": "DF_EAR_GGAP_SEX_OCU_RT",
    },
    # ===========================================
    # WORKING TIME
    # ===========================================
    "HOW_TEMP_SEX_ECO_NB": {
        "name": "Mean weekly hours worked by sex",
        "category": "working_time",
        "sdmx_flow": "DF_HOW_TEMP_SEX_ECO_NB",
    },
    "TRU_DEMP_SEX_AGE_RT": {
        "name": "Time-related underemployment rate by sex",
        "category": "working_time",
        "sdmx_flow": "DF_TRU_DEMP_SEX_AGE_RT",
    },
    # ===========================================
    # INFORMALITY
    # ===========================================
    "EMP_NIFL_SEX_RT": {
        "name": "Informal employment rate by sex",
        "category": "informal",
        "sdmx_flow": "DF_EMP_NIFL_SEX_RT",
    },
    # ===========================================
    # SOCIAL PROTECTION (SDG Indicator)
    # ===========================================
    "SDG_0131_SEX_SOC_RT": {
        "name": "Social protection coverage by sex",
        "category": "social_protection",
        "sdmx_flow": "DF_SDG_0131_SEX_SOC_RT",
    },
}

# Countries - Focus on major economies and all of Asia
COUNTRIES = [
    # Major Asian Countries
    "CHN",
    "JPN",
    "KOR",
    "IND",
    "IDN",
    "THA",
    "VNM",
    "MYS",
    "SGP",
    "PHL",
    "PAK",
    "BGD",
    "LKA",
    "NPL",
    "MMR",
    "KHM",
    "LAO",
    "MNG",
    "HKG",
    "TWN",
    # Middle East & Central Asia
    "ARE",
    "SAU",
    "IRN",
    "IRQ",
    "ISR",
    "TUR",
    "KAZ",
    "UZB",
    "AFG",
    # Americas
    "USA",
    "CAN",
    "MEX",
    "BRA",
    "ARG",
    "CHL",
    "COL",
    "PER",
    # Europe
    "DEU",
    "FRA",
    "GBR",
    "ITA",
    "ESP",
    "RUS",
    "POL",
    "NLD",
    # Africa
    "ZAF",
    "NGA",
    "EGY",
    "KEN",
    "ETH",
    # Oceania
    "AUS",
    "NZL",
]


def fetch_ilo_data_bulk(indicator_id: str) -> List[Dict]:
    """Fetch ILO data via bulk download API"""

    # ILO provides bulk CSV/JSON downloads
    base_url = "https://rplumber.ilo.org/data/indicator/"

    url = f"{base_url}?id={indicator_id}&format=json"

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, headers=headers, timeout=120)

        if response.status_code != 200:
            return []

        data = response.json()

        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data:
            return data["data"]
        return []

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def fetch_ilo_via_worldbank(indicator_code: str, wb_code: str = None) -> List[Dict]:
    """Fetch ILO-compatible data via World Bank API (more reliable)"""

    # World Bank has many ILO indicators
    wb_labor_indicators = {
        "EAP_DWAP_SEX_AGE_RT": "SL.TLF.CACT.FE.ZS",  # Female labor participation
        "UNE_DEAP_SEX_AGE_RT": "SL.UEM.TOTL.FE.ZS",  # Female unemployment
        "EMP_DWAP_SEX_AGE_RT": "SL.EMP.TOTL.SP.FE.ZS",  # Female employment ratio
    }

    wb_code = wb_code or wb_labor_indicators.get(indicator_code)
    if not wb_code:
        return []

    base_url = "https://api.worldbank.org/v2"
    country_str = ";".join(COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{wb_code}"
    params = {"format": "json", "per_page": 5000, "date": "2000:2024"}

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception:
        return []


def save_to_database(conn, records: List[Dict], indicator_id: str, indicator_info: Dict, source: str = "ILO") -> int:
    """Save ILO women's labor data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.women_ilo_data (
            id SERIAL PRIMARY KEY,
            indicator_id VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            country_code VARCHAR(10),
            country_name VARCHAR(100),
            sex VARCHAR(20),
            age_group VARCHAR(50),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(50) DEFAULT 'ILO',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_id, country_code, sex, age_group, year)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ilo_indicator_year
        ON sofia.women_ilo_data(indicator_id, year DESC)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ilo_country
        ON sofia.women_ilo_data(country_code)
    """
    )

    inserted = 0

    for record in records:
        # Handle different record formats (ILO vs World Bank)
        if "ref_area" in record:
            # ILO format
            country_code = (
                record.get("ref_area", {}).get("id", "")
                if isinstance(record.get("ref_area"), dict)
                else record.get("ref_area", "")
            )
            country_name = (
                record.get("ref_area", {}).get("label", "") if isinstance(record.get("ref_area"), dict) else ""
            )
            sex = (
                record.get("sex", {}).get("id", "T") if isinstance(record.get("sex"), dict) else record.get("sex", "T")
            )
            age = record.get("classif1", {}).get("id", "TOTAL") if isinstance(record.get("classif1"), dict) else "TOTAL"
            year = record.get("time", "")
            value = record.get("obs_value")
        else:
            # World Bank format
            country_code = record.get("countryiso3code", record.get("country", {}).get("id", ""))
            country_name = record.get("country", {}).get("value", "")
            sex = "F"  # World Bank indicators are already female-specific
            age = "TOTAL"
            year = record.get("date", "")
            value = record.get("value")

        if value is None:
            continue

        if country_code not in COUNTRIES:
            continue

        try:
            cursor.execute(
                """
                INSERT INTO sofia.women_ilo_data
                (indicator_id, indicator_name, category, country_code, country_name, sex, age_group, year, value, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_id, country_code, sex, age_group, year)
                DO UPDATE SET value = EXCLUDED.value
            """,
                (
                    indicator_id,
                    indicator_info.get("name", ""),
                    indicator_info.get("category", "other"),
                    country_code,
                    country_name,
                    sex,
                    age,
                    int(year) if year and str(year).isdigit() else None,
                    float(value),
                    source,
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
    print("ILO WOMEN'S LABOR DATA - ILOSTAT")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: International Labour Organization (ILO)")
    print(f"API: https://ilostat.ilo.org/")
    print("")
    print(f"Indicators: {len(ILO_WOMEN_INDICATORS)}")
    print(f"Countries: {len(COUNTRIES)} (focus on Asia + major economies)")
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
    for ind_id, info in ILO_WOMEN_INDICATORS.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((ind_id, info))

    for cat_name, indicators in categories.items():
        print(f"--- {cat_name.upper().replace('_', ' ')} ---")
        for indicator_id, indicator_info in indicators:
            print(f"  {indicator_info['name'][:55]}...")

            # Try ILO bulk first
            records = fetch_ilo_data_bulk(indicator_id)
            source = "ILO"

            # If no ILO data, try World Bank
            if not records:
                records = fetch_ilo_via_worldbank(indicator_id)
                source = "World Bank/ILO"

            if records:
                print(f"    Fetched: {len(records)} records ({source})")
                inserted = save_to_database(conn, records, indicator_id, indicator_info, source)
                total_records += inserted
                successful += 1
                print(f"    Saved: {inserted} records")
            else:
                failed += 1
                print(f"    No data")
        print("")

    conn.close()

    print("=" * 80)
    print("ILO WOMEN'S LABOR DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful indicators: {successful}")
    print(f"Failed indicators: {failed}")
    print("")
    print("Categories covered:")
    print("  - Labor Force Participation")
    print("  - Employment by Sector & Status")
    print("  - Unemployment by Age")
    print("  - Earnings & Gender Wage Gap")
    print("  - Working Time")
    print("  - Informal Employment")
    print("  - Social Protection")
    print("")
    print("Asia focus:")
    print("  China, Japan, Korea, India, Indonesia, Thailand")
    print("  Vietnam, Malaysia, Singapore, Philippines, Pakistan")
    print("  Bangladesh, Hong Kong, Taiwan, UAE, Saudi Arabia")


if __name__ == "__main__":
    main()
