#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
Brazilian Women's Data Collector - IBGE, IPEA, Secretaria da Mulher
Coleta dados especificos de mulheres no Brasil

APIs:
- IBGE SIDRA: https://apisidra.ibge.gov.br/
- IPEA: http://www.ipeadata.gov.br/api/
- Portal Brasileiro de Dados Abertos: https://dados.gov.br/
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

# IBGE SIDRA Tables for Women's Data
# Reference: https://sidra.ibge.gov.br/
IBGE_WOMEN_TABLES = {
    # PNAD Continua - Labor Market
    "6402": {
        "name": "Taxa de desocupacao por sexo",
        "category": "labor",
        "description": "Unemployment rate by sex - PNAD Continua",
    },
    "6378": {"name": "Pessoas ocupadas por sexo", "category": "labor", "description": "Employed persons by sex"},
    "6387": {"name": "Rendimento medio por sexo", "category": "earnings", "description": "Average earnings by sex"},
    "6394": {
        "name": "Taxa de participacao por sexo",
        "category": "labor",
        "description": "Labor force participation rate by sex",
    },
    # Education
    "7267": {
        "name": "Taxa de frequencia escolar por sexo",
        "category": "education",
        "description": "School attendance rate by sex",
    },
    # Violence (Pesquisa Nacional de Saude)
    "7654": {
        "name": "Pessoas que sofreram violencia",
        "category": "violence",
        "description": "Persons who suffered violence",
    },
    # Demographics
    "6579": {
        "name": "Populacao por sexo e idade",
        "category": "demographics",
        "description": "Population by sex and age",
    },
    # Health (PNS)
    "7665": {"name": "Consultas pre-natal", "category": "health", "description": "Prenatal consultations"},
}

# IPEA Series for Women's Data
# Reference: http://www.ipeadata.gov.br/
IPEA_WOMEN_SERIES = {
    # Labor Market
    "PNADC12_TDESam": {
        "name": "Taxa de desemprego - Mulheres",
        "category": "labor",
        "description": "Female unemployment rate",
    },
    "PNADC12_TOCUM": {
        "name": "Taxa de ocupacao - Mulheres",
        "category": "labor",
        "description": "Female employment rate",
    },
    "PNADC12_RNMM": {
        "name": "Rendimento medio - Mulheres",
        "category": "earnings",
        "description": "Female average earnings",
    },
    # Education
    "PNADC12_TALFM": {
        "name": "Taxa de alfabetizacao - Mulheres",
        "category": "education",
        "description": "Female literacy rate",
    },
    # Violence (from DataSUS)
    "SIM_HOMICM": {
        "name": "Homicidios de mulheres",
        "category": "violence",
        "description": "Female homicides (feminicide proxy)",
    },
    # Fertility
    "IBGE12_TXFECT": {"name": "Taxa de fecundidade total", "category": "health", "description": "Total fertility rate"},
    # Maternal mortality
    "SIM_MORTMAT": {
        "name": "Taxa de mortalidade materna",
        "category": "health",
        "description": "Maternal mortality rate",
    },
}


def fetch_ibge_sidra(table_id: str) -> List[Dict]:
    """Fetch data from IBGE SIDRA API"""

    # SIDRA API format
    base_url = "https://apisidra.ibge.gov.br/values"

    # Try to get data with sex breakdown
    url = f"{base_url}/t/{table_id}/n1/all/p/last%2020/v/all"

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, headers=headers, timeout=60)

        if response.status_code != 200:
            # Try alternative format
            url = f"{base_url}/t/{table_id}/n1/all/p/last%2012"
            response = requests.get(url, headers=headers, timeout=60)

        if response.status_code != 200:
            return []

        data = response.json()

        if isinstance(data, list) and len(data) > 1:
            return data[1:]  # Skip header row
        return []

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def fetch_ipea_series(series_code: str) -> List[Dict]:
    """Fetch data from IPEA API"""

    base_url = "http://www.ipeadata.gov.br/api/odata4"

    url = f"{base_url}/ValoresSerie(SERCODIGO='{series_code}')"

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, headers=headers, timeout=60)

        if response.status_code != 200:
            return []

        data = response.json()

        if "value" in data:
            return data["value"]
        return []

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def save_ibge_to_database(conn, records: List[Dict], table_id: str, table_info: Dict) -> int:
    """Save IBGE SIDRA women's data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.women_brazil_data (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            source VARCHAR(20) NOT NULL,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            region VARCHAR(100),
            period VARCHAR(20),
            sex VARCHAR(20),
            value DECIMAL(18, 6),
            unit VARCHAR(50),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, indicator_code, region, period, sex)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_brazil_women_indicator
        ON sofia.women_brazil_data(indicator_code)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_brazil_women_period
        ON sofia.women_brazil_data(period DESC)
    """
    )

    inserted = 0
    errors = 0

    for record in records:
        if not isinstance(record, dict):
            continue

        # SIDRA format parsing
        value = record.get("V", record.get("value"))
        if value in [None, "-", "...", "X"]:
            continue

        try:
            # Extract fields from SIDRA response
            period = record.get("D2C", record.get("periodo", ""))
            region = record.get("D1N", record.get("localidade", "Brasil"))
            sex = record.get("D3N", record.get("sexo", "Total"))
            unit = record.get("MN", record.get("unidade", ""))

            # Normalize Brazil (region is state)
            location = normalize_location(conn, {"country": "Brazil", "state": region})
            country_id = location.get("country_id")

            cursor.execute(
                """
                INSERT INTO sofia.women_brazil_data (source, indicator_code, indicator_name, category, region, period, sex, value, unit, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, indicator_code, region, period, sex)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """,
                (
                    "IBGE",
                    table_id,
                    table_info.get("name", ""),
                    table_info.get("category", "other"),
                    region,
                    period,
                    sex,
                    float(str(value).replace(",", ".")) if value else None,
                    unit,
                    country_id,
                ),
            )
            inserted += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"      ERROR (IBGE): {str(e)[:100]}")
            continue

    conn.commit()
    cursor.close()
    return inserted


def save_ipea_to_database(conn, records: List[Dict], series_code: str, series_info: Dict) -> int:
    """Save IPEA women's data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Use same table as IBGE
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.women_brazil_data (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            source VARCHAR(20) NOT NULL,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            category VARCHAR(50),
            region VARCHAR(100),
            period VARCHAR(20),
            sex VARCHAR(20),
            value DECIMAL(18, 6),
            unit VARCHAR(50),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, indicator_code, region, period, sex)
        )
    """
    )

    # Normalize Brazil once (all IPEA data is Brazil-level)
    location = normalize_location(conn, {"country": "Brazil"})
    country_id = location.get("country_id")

    inserted = 0
    errors = 0

    for record in records:
        value = record.get("VALVALOR")
        if value is None:
            continue

        try:
            # IPEA format
            date = record.get("VALDATA", "")
            if date:
                # Convert IPEA date format to period
                period = date[:7] if len(date) >= 7 else date[:4]
            else:
                continue

            cursor.execute(
                """
                INSERT INTO sofia.women_brazil_data (source, indicator_code, indicator_name, category, region, period, sex, value, unit, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, indicator_code, region, period, sex)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """,
                (
                    "IPEA",
                    series_code,
                    series_info.get("name", ""),
                    series_info.get("category", "other"),
                    "Brasil",
                    period,
                    "Mulheres",
                    float(value),
                    "",
                    country_id,
                ),
            )
            inserted += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"      ERROR (IPEA): {str(e)[:100]}")
            continue

    conn.commit()
    cursor.close()
    return inserted


def fetch_datasus_violence() -> List[Dict]:
    """Fetch violence against women data from DataSUS/TabNet"""

    # DataSUS violence data (femicide, domestic violence)
    # Using World Bank as fallback for maternal mortality
    base_url = "https://api.worldbank.org/v2"

    url = f"{base_url}/country/BRA/indicator/SH.STA.MMRT"
    params = {"format": "json", "per_page": 100, "date": "2000:2024"}

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception:
        return []


def main():
    print("=" * 80)
    print("BRAZILIAN WOMEN'S DATA - IBGE, IPEA, DATASUS")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources:")
    print(f"  - IBGE SIDRA: https://sidra.ibge.gov.br/")
    print(f"  - IPEA: http://www.ipeadata.gov.br/")
    print(f"  - DataSUS: http://datasus.saude.gov.br/")
    print("")
    print(f"IBGE Tables: {len(IBGE_WOMEN_TABLES)}")
    print(f"IPEA Series: {len(IPEA_WOMEN_SERIES)}")
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

    # IBGE SIDRA
    print("--- IBGE SIDRA ---")
    for table_id, table_info in IBGE_WOMEN_TABLES.items():
        print(f"  Table {table_id}: {table_info['name'][:45]}...")

        records = fetch_ibge_sidra(table_id)

        if records:
            print(f"    Fetched: {len(records)} records")
            inserted = save_ibge_to_database(conn, records, table_id, table_info)
            total_records += inserted
            successful += 1
            print(f"    Saved: {inserted} records")
        else:
            failed += 1
            print(f"    No data")
    print("")

    # IPEA
    print("--- IPEA ---")
    for series_code, series_info in IPEA_WOMEN_SERIES.items():
        print(f"  {series_info['name'][:50]}...")

        records = fetch_ipea_series(series_code)

        if records:
            print(f"    Fetched: {len(records)} records")
            inserted = save_ipea_to_database(conn, records, series_code, series_info)
            total_records += inserted
            successful += 1
            print(f"    Saved: {inserted} records")
        else:
            failed += 1
            print(f"    No data")
    print("")

    # DataSUS / Violence data
    print("--- VIOLENCE DATA ---")
    print("  Maternal mortality (World Bank)...")
    records = fetch_datasus_violence()
    if records:
        print(f"    Fetched: {len(records)} records")
        # Save using IPEA function
        cursor = conn.cursor()

        # Normalize Brazil once
        location = normalize_location(conn, {"country": "Brazil"})
        country_id = location.get("country_id")

        datasus_errors = 0
        for r in records:
            if r.get("value"):
                try:
                    cursor.execute(
                        """
                        INSERT INTO sofia.women_brazil_data (source, indicator_code, indicator_name, category, region, period, sex, value, unit, country_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source, indicator_code, region, period, sex)
                        DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
                    """,
                        (
                            "World Bank",
                            "SH.STA.MMRT",
                            "Maternal mortality ratio (per 100,000 live births)",
                            "health",
                            "Brasil",
                            r.get("date", ""),
                            "Mulheres",
                            float(r.get("value")),
                            "per 100,000",
                            country_id,
                        ),
                    )
                    total_records += 1
                except Exception as e:
                    datasus_errors += 1
                    if datasus_errors <= 3:
                        print(f"      ERROR (DataSUS): {str(e)[:100]}")
                    pass
        conn.commit()
        cursor.close()
        print(f"    Saved records")
    print("")

    conn.close()

    print("=" * 80)
    print("BRAZILIAN WOMEN'S DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful sources: {successful}")
    print(f"Failed sources: {failed}")
    print("")
    print("Categories covered:")
    print("  - Labor Market (unemployment, employment, participation)")
    print("  - Earnings (gender wage gap)")
    print("  - Education (literacy, school attendance)")
    print("  - Health (maternal mortality, prenatal care)")
    print("  - Violence (homicides, domestic violence)")
    print("  - Demographics (population by sex)")


if __name__ == "__main__":
    main()
