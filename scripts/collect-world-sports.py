#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
World Sports Data Collector
Coleta dados de participacao esportiva por genero e indicadores socioeconomicos

Fontes Oficiais:
- UNESCO Institute of Statistics
- WHO Global Health Observatory (Physical Activity)
- Eurostat (EU Sports participation)
- World Bank (socioeconomic indicators of athletes)
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

# Countries for sports data
COUNTRIES = [
    # Americas
    "USA",
    "CAN",
    "BRA",
    "MEX",
    "ARG",
    "COL",
    "CHL",
    "PER",
    "VEN",
    "ECU",
    # Europe
    "DEU",
    "GBR",
    "FRA",
    "ITA",
    "ESP",
    "NLD",
    "BEL",
    "SWE",
    "NOR",
    "DNK",
    "POL",
    "PRT",
    "AUT",
    "CHE",
    "FIN",
    "IRL",
    "GRC",
    "CZE",
    "HUN",
    "ROU",
    # Asia
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
    # Others
    "AUS",
    "NZL",
    "ZAF",
    "EGY",
    "NGA",
    "KEN",
]

# WHO Physical Activity Indicators
WHO_ACTIVITY_INDICATORS = [
    # Physical activity levels by sex
    {
        "code": "NCD_PAC_ADO",
        "name": "Adolescents insufficiently physically active (%)",
        "category": "physical_activity",
    },
    {"code": "NCD_PAA_ADO", "name": "Adolescents sufficiently active (%)", "category": "physical_activity"},
    {
        "code": "NCD_PAC_ADO_FE",
        "name": "Adolescents insufficiently active, female (%)",
        "category": "physical_activity",
    },
    {"code": "NCD_PAC_ADO_MA", "name": "Adolescents insufficiently active, male (%)", "category": "physical_activity"},
]

# Eurostat Sports Participation Datasets
EUROSTAT_SPORTS_DATASETS = {
    "HLTH_EHIS_PE1E": {
        "name": "Persons performing health-enhancing physical activities by sex",
        "category": "participation",
    },
    "HLTH_EHIS_PE2E": {
        "name": "Persons performing muscle-strengthening activities by sex",
        "category": "participation",
    },
    "HLTH_EHIS_PE3E": {"name": "Frequency of physical activity by sex", "category": "participation"},
    "CULT_PCS_SPO": {
        "name": "Participation in sports activities by socioeconomic characteristics",
        "category": "participation",
    },
}

# World Bank socioeconomic indicators related to sports
SOCIOECONOMIC_INDICATORS = {
    # Health & Lifestyle
    "SH.STA.OWGH.ZS": {
        "name": "Prevalence of overweight (% of adults)",
        "category": "health",
        "description": "Overweight adults - related to physical activity",
    },
    "SH.STA.OWGH.FE.ZS": {
        "name": "Prevalence of overweight, female (% of female adults)",
        "category": "health",
        "description": "Overweight female adults",
    },
    "SH.STA.OWGH.MA.ZS": {
        "name": "Prevalence of overweight, male (% of male adults)",
        "category": "health",
        "description": "Overweight male adults",
    },
    "NCD_BMI_30A": {
        "name": "Prevalence of obesity (BMI >= 30)",
        "category": "health",
        "description": "Obesity prevalence",
    },
    # Income & Employment
    "NY.GDP.PCAP.CD": {
        "name": "GDP per capita (current US$)",
        "category": "economic",
        "description": "Economic indicator - sports participation correlates with income",
    },
    "SL.UEM.TOTL.ZS": {"name": "Unemployment, total (%)", "category": "economic", "description": "Unemployment rate"},
    # Education
    "SE.TER.ENRR": {
        "name": "School enrollment, tertiary (% gross)",
        "category": "education",
        "description": "Higher education - correlates with sports participation",
    },
    # Leisure time (proxy)
    "SL.TLF.PART.FE.ZS": {
        "name": "Part-time employment, female (%)",
        "category": "work_life",
        "description": "Part-time work allows more leisure for sports",
    },
    # Life expectancy (outcome of active lifestyle)
    "SP.DYN.LE00.IN": {
        "name": "Life expectancy at birth",
        "category": "health_outcome",
        "description": "Physical activity increases life expectancy",
    },
}


def fetch_who_data(indicator_code: str) -> List[Dict]:
    """Fetch physical activity data from WHO GHO API"""

    base_url = "https://ghoapi.azureedge.net/api"
    url = f"{base_url}/{indicator_code}"

    country_filter = "','".join(COUNTRIES)
    params = {"$filter": f"SpatialDim in ('{country_filter}')"}

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=60)

        if response.status_code != 200:
            # Try without filter
            response = requests.get(url, headers=headers, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if "value" in data:
                return data["value"]
        return []

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def fetch_worldbank_data(indicator_code: str) -> List[Dict]:
    """Fetch socioeconomic data from World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ";".join(COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 3000, "date": "2010:2024", "source": 2}

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception:
        return []


def fetch_eurostat_sports() -> List[Dict]:
    """Fetch EU sports participation data from Eurostat"""

    records = []

    for dataset_code, dataset_info in EUROSTAT_SPORTS_DATASETS.items():
        base_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
        url = f"{base_url}/{dataset_code}"
        params = {"format": "JSON", "lang": "en"}

        try:
            response = requests.get(url, params=params, timeout=120)
            if response.status_code == 200:
                data = response.json()
                # Process Eurostat JSON-stat format
                if "value" in data:
                    for idx, value in data["value"].items():
                        if value is not None:
                            records.append(
                                {
                                    "dataset": dataset_code,
                                    "dataset_name": dataset_info["name"],
                                    "category": dataset_info["category"],
                                    "value": value,
                                    "source": "Eurostat",
                                }
                            )
        except Exception:
            continue

    return records


def save_who_data(conn, records: List[Dict], indicator: Dict) -> int:
    """Save WHO physical activity data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.world_sports_data (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            source VARCHAR(50) NOT NULL,
            indicator_code VARCHAR(100),
            indicator_name TEXT,
            category VARCHAR(50),
            country_code VARCHAR(10),
            sex VARCHAR(20),
            year INTEGER,
            value DECIMAL(18, 6),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, indicator_code, country_code, sex, year)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sports_source_country
        ON sofia.world_sports_data(source, country_code)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sports_category
        ON sofia.world_sports_data(category)
    """
    )

    inserted = 0

    for record in records:
        value = record.get("NumericValue")
        if value is None:
            continue

        country = record.get("SpatialDim", "")
        if country not in COUNTRIES:
            continue

        try:
            # Normalize country
            location = normalize_location(conn, {"country": country_code})
            country_id = location["country_id"]

            cursor.execute(
                """
                INSERT INTO sofia.world_sports_data (source, indicator_code, indicator_name, category, country_code, sex, year, value, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, indicator_code, country_code, sex, year)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """,
                (
                    "WHO",
                    indicator.get("code", ""),
                    indicator.get("name", ""),
                    indicator.get("category", "physical_activity"),
                    country,
                    record.get("Dim1", "BTSX"),
                    int(record.get("TimeDim", 0)) if record.get("TimeDim") else None,
                    float(value),
                    country_id,
                ),
            )
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def save_worldbank_data(conn, records: List[Dict], indicator_code: str, indicator_info: Dict) -> int:
    """Save World Bank socioeconomic data"""

    if not records:
        return 0

    cursor = conn.cursor()

    inserted = 0

    for record in records:
        value = record.get("value")
        if value is None:
            continue

        try:
            cursor.execute(
                """
                INSERT INTO sofia.world_sports_data (source, indicator_code, indicator_name, category, country_code, sex, year, value, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, indicator_code, country_code, sex, year)
                DO UPDATE SET value = EXCLUDED.value
            """,
                (
                    "World Bank",
                    indicator_code,
                    indicator_info.get("name", "", country_id=EXCLUDED.country_id),
                    indicator_info.get("category", "economic"),
                    record.get("countryiso3code", record.get("country", {}).get("id")),
                    "BTSX",  # Both sexes for general indicators
                    int(record.get("date")) if record.get("date") else None,
                    float(value),
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
    print("WORLD SPORTS & PHYSICAL ACTIVITY DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources:")
    print(f"  - WHO Global Health Observatory (Physical Activity)")
    print(f"  - Eurostat (EU Sports Participation)")
    print(f"  - World Bank (Socioeconomic indicators)")
    print("")
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

    # 1. WHO Physical Activity Data
    print("=== WHO PHYSICAL ACTIVITY ===")
    for indicator in WHO_ACTIVITY_INDICATORS:
        print(f"  {indicator['name'][:55]}...")

        records = fetch_who_data(indicator["code"])

        if records:
            print(f"    Fetched: {len(records)} records")
            inserted = save_who_data(conn, records, indicator)
            total_records += inserted
            print(f"    Saved: {inserted} records")
        else:
            print(f"    No data")
    print("")

    # 2. Eurostat Sports Participation
    print("=== EUROSTAT SPORTS PARTICIPATION (EU) ===")
    print("  Fetching EU sports participation surveys...")
    eurostat_data = fetch_eurostat_sports()
    if eurostat_data:
        print(f"    Fetched: {len(eurostat_data)} records")
        # Save Eurostat data
        cursor = conn.cursor()
        for r in eurostat_data:
            try:
                cursor.execute(
                    """
                    INSERT INTO sofia.world_sports_data (source, indicator_code, indicator_name, category, country_code, sex, year, value, country_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, indicator_code, country_code, sex, year)
                    DO UPDATE SET value = EXCLUDED.value
                """,
                    (
                        "Eurostat",
                        r.get("dataset", "", country_id=EXCLUDED.country_id),
                        r.get("dataset_name", ""),
                        r.get("category", "participation"),
                        "EU",
                        "BTSX",
                        2022,
                        float(r.get("value", 0)),
                    ),
                )
                total_records += 1
            except:
                continue
        conn.commit()
        cursor.close()
        print(f"    Saved records")
    print("")

    # 3. Socioeconomic Indicators
    print("=== SOCIOECONOMIC INDICATORS ===")
    for indicator_code, indicator_info in SOCIOECONOMIC_INDICATORS.items():
        print(f"  {indicator_info['name'][:55]}...")

        records = fetch_worldbank_data(indicator_code)

        if records:
            print(f"    Fetched: {len(records)} records")
            inserted = save_worldbank_data(conn, records, indicator_code, indicator_info)
            total_records += inserted
            print(f"    Saved: {inserted} records")
        else:
            print(f"    No data")
    print("")

    conn.close()

    print("=" * 80)
    print("WORLD SPORTS DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Data collected:")
    print("")
    print("Physical Activity (WHO):")
    print("  - Insufficient physical activity by sex")
    print("  - Adolescent physical activity levels")
    print("  - Male vs Female activity rates")
    print("")
    print("Sports Participation (Eurostat EU):")
    print("  - Health-enhancing physical activities by sex")
    print("  - Muscle-strengthening activities by sex")
    print("  - Frequency of physical activity")
    print("  - Participation by socioeconomic characteristics")
    print("")
    print("Socioeconomic Indicators (World Bank):")
    print("  - Overweight prevalence (total, male, female)")
    print("  - Obesity prevalence")
    print("  - GDP per capita (income level)")
    print("  - Unemployment rate")
    print("  - Tertiary education enrollment")
    print("  - Part-time employment (leisure time)")
    print("  - Life expectancy")
    print("")
    print("Table created: sofia.world_sports_data")


if __name__ == "__main__":
    main()
