#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
European Gender Data Collector - Eurostat
Coleta dados de genero da Uniao Europeia via Eurostat API

API: https://ec.europa.eu/eurostat/api/
Portal: https://ec.europa.eu/eurostat/web/gender-equality
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

# Eurostat Gender Datasets
# Reference: https://ec.europa.eu/eurostat/web/gender-equality/data/database
EUROSTAT_DATASETS = {
    # Gender Pay Gap
    "SDG_05_20": {
        "name": "Gender pay gap in unadjusted form",
        "category": "economic",
        "description": "Difference between average gross hourly earnings of male and female employees",
    },
    "EARN_GR_GPGR2": {
        "name": "Gender pay gap by economic activity",
        "category": "economic",
        "description": "Pay gap breakdown by NACE sector",
    },
    # Employment
    "LFSI_EMP_A": {
        "name": "Employment rate by sex and age",
        "category": "labor",
        "description": "Employment rates for different age groups",
    },
    "LFSA_ERGAN": {
        "name": "Employment rates by sex, age and citizenship",
        "category": "labor",
        "description": "Detailed employment rates",
    },
    "LFSA_EPGAED": {
        "name": "Employment by sex and education",
        "category": "labor",
        "description": "Employment by educational attainment",
    },
    # Part-time and Temporary Work
    "LFSA_EPPGA": {
        "name": "Part-time employment by sex and age",
        "category": "labor",
        "description": "Part-time workers as percentage",
    },
    "LFSA_ETPGA": {
        "name": "Temporary employment by sex and age",
        "category": "labor",
        "description": "Temporary contracts by gender",
    },
    # Unemployment
    "UNE_RT_A": {
        "name": "Unemployment rates by sex and age",
        "category": "labor",
        "description": "Annual unemployment rates",
    },
    # Education
    "EDUC_UOE_GRAD02": {
        "name": "Graduates by education level and sex",
        "category": "education",
        "description": "Number of graduates by field",
    },
    "EDAT_LFSE_03": {
        "name": "Population by education attainment and sex",
        "category": "education",
        "description": "Educational attainment levels",
    },
    "ISOC_SK_DSKL_I": {
        "name": "Digital skills by sex",
        "category": "education",
        "description": "Digital skills indicator",
    },
    # Leadership and Decision-making
    "SDG_05_60": {
        "name": "Positions held by women in senior management",
        "category": "political",
        "description": "Women in management positions",
    },
    "SDG_05_50": {
        "name": "Seats held by women in national parliaments",
        "category": "political",
        "description": "Women MPs percentage",
    },
    # Work-life Balance
    "LFSO_16INACTPT": {
        "name": "Inactive persons due to caring responsibilities",
        "category": "work_life",
        "description": "People out of labor force due to care duties",
    },
    # Poverty and Social Exclusion
    "ILC_PEPS01N": {
        "name": "At-risk-of-poverty rate by sex",
        "category": "poverty",
        "description": "Poverty risk by gender",
    },
    "ILC_LI02": {
        "name": "At-risk-of-poverty rate by sex and age",
        "category": "poverty",
        "description": "Detailed poverty rates",
    },
    # Health
    "HLTH_SILC_17": {
        "name": "Self-perceived health by sex",
        "category": "health",
        "description": "Health perception indicator",
    },
    "DEMO_MLEXPEC": {"name": "Life expectancy by sex", "category": "health", "description": "Life expectancy at birth"},
    # Violence (Survey based)
    "CRIM_GEN_REG": {
        "name": "Gender-based violence statistics",
        "category": "violence",
        "description": "Violence against women data",
    },
}

# EU Countries
EU_COUNTRIES = [
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "EL",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
    # Non-EU European
    "NO",
    "IS",
    "CH",
    "UK",
    "RS",
    "TR",
    "ME",
    "MK",
    "AL",
    "BA",
]


def fetch_eurostat_data(dataset_code: str) -> List[Dict]:
    """Fetch data from Eurostat JSON API"""

    # Eurostat JSON-stat API
    base_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

    url = f"{base_url}/{dataset_code}"
    params = {
        "format": "JSON",
        "lang": "en",
    }

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=120)

        if response.status_code == 404:
            print(f"    Dataset not found or restricted")
            return []

        response.raise_for_status()
        data = response.json()

        # Parse JSON-stat format
        records = parse_jsonstat(data, dataset_code)
        return records

    except Exception as e:
        print(f"    Error: {str(e)[:100]}")
        return []


def parse_jsonstat(data: Dict, dataset_code: str) -> List[Dict]:
    """Parse Eurostat JSON-stat format into flat records"""

    records = []

    if "value" not in data or "dimension" not in data:
        return records

    values = data.get("value", {})
    dimensions = data.get("dimension", {})
    dimension_ids = data.get("id", [])
    data.get("size", [])

    if not values or not dimensions:
        return records

    # Get dimension categories
    dim_categories = {}
    for dim_id in dimension_ids:
        dim_data = dimensions.get(dim_id, {})
        category = dim_data.get("category", {})
        labels = category.get("label", {})
        index = category.get("index", {})

        # Create index to label mapping
        if isinstance(index, dict):
            idx_to_label = {v: labels.get(k, k) for k, v in index.items()}
            idx_to_code = {v: k for k, v in index.items()}
        else:
            idx_to_label = labels
            idx_to_code = {i: k for i, k in enumerate(labels.keys())}

        dim_categories[dim_id] = {"labels": idx_to_label, "codes": idx_to_code, "size": len(labels)}

    # Convert flat values to records
    for idx_str, value in values.items():
        if value is None:
            continue

        idx = int(idx_str)

        # Calculate multi-dimensional indices
        indices = []
        remaining = idx
        for dim_id in reversed(dimension_ids):
            size = dim_categories[dim_id]["size"]
            indices.insert(0, remaining % size)
            remaining //= size

        # Build record
        record = {"dataset": dataset_code, "value": value}

        for i, dim_id in enumerate(dimension_ids):
            dim_idx = indices[i]
            record[f"{dim_id}_code"] = dim_categories[dim_id]["codes"].get(dim_idx, "")
            record[f"{dim_id}_label"] = dim_categories[dim_id]["labels"].get(dim_idx, "")

        # Extract key fields
        record["country"] = record.get("geo_code", record.get("GEO_code", ""))
        record["year"] = record.get("time_code", record.get("TIME_PERIOD_code", ""))
        record["sex"] = record.get("sex_code", record.get("SEX_code", ""))

        records.append(record)

    return records


def save_to_database(conn, records: List[Dict], dataset_info: Dict) -> int:
    """Save Eurostat gender data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.women_eurostat_data (
            id SERIAL PRIMARY KEY,
            dataset_code VARCHAR(50) NOT NULL,
            dataset_name TEXT,
            category VARCHAR(50),
            country_code VARCHAR(10),
            year VARCHAR(10),
            sex VARCHAR(20),
            age_group VARCHAR(50),
            value DECIMAL(18, 6),
            unit VARCHAR(50),
            source VARCHAR(50) DEFAULT 'Eurostat',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dataset_code, country_code, year, sex, age_group)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_eurostat_dataset
        ON sofia.women_eurostat_data(dataset_code)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_eurostat_country_year
        ON sofia.women_eurostat_data(country_code, year DESC)
    """
    )

    inserted = 0

    for record in records:
        country = record.get("country", "")
        if not country or country not in EU_COUNTRIES:
            continue

        try:
            year = record.get("year", "")
            if year and len(year) >= 4:
                year = year[:4]  # Extract year from formats like "2023" or "2023Q1"

            # Normalize country to get country_id
            location = normalize_location(conn, {"country": country})
            country_id = location["country_id"]

            cursor.execute(
                """
                INSERT INTO sofia.women_eurostat_data
                (dataset_code, dataset_name, category, country_code, country_id, year, sex, age_group, value, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (dataset_code, country_code, year, sex, age_group)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """,
                (
                    record.get("dataset", ""),
                    dataset_info.get("name", ""),
                    dataset_info.get("category", "other"),
                    country,
                    country_id,
                    year,
                    record.get("sex", "T"),
                    record.get("age_code", record.get("AGE_code", "TOTAL")),
                    float(record.get("value", 0)),
                    record.get("unit_code", record.get("UNIT_code", "")),
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
    print("EUROPEAN GENDER DATA - EUROSTAT")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: Eurostat Gender Equality Portal")
    print(f"API: https://ec.europa.eu/eurostat/api/")
    print("")
    print(f"Datasets: {len(EUROSTAT_DATASETS)}")
    print(f"Countries: {len(EU_COUNTRIES)} (EU + European)")
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
    for code, info in EUROSTAT_DATASETS.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((code, info))

    for cat_name, datasets in categories.items():
        print(f"--- {cat_name.upper()} ---")
        for dataset_code, dataset_info in datasets:
            print(f"  {dataset_info['name'][:55]}...")

            records = fetch_eurostat_data(dataset_code)

            if records:
                print(f"    Fetched: {len(records)} records")
                inserted = save_to_database(conn, records, dataset_info)
                total_records += inserted
                successful += 1
                print(f"    Saved: {inserted} records")
            else:
                failed += 1
                print(f"    No data or error")
        print("")

    conn.close()

    print("=" * 80)
    print("EUROSTAT GENDER DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful datasets: {successful}")
    print(f"Failed/Empty datasets: {failed}")
    print("")
    print("Categories covered:")
    print("  - Gender Pay Gap (SDG 5.20)")
    print("  - Employment & Labor Force")
    print("  - Education & Digital Skills")
    print("  - Leadership & Politics")
    print("  - Work-Life Balance")
    print("  - Poverty & Social Exclusion")
    print("  - Health")


if __name__ == "__main__":
    main()
