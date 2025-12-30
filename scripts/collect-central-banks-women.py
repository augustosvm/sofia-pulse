#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
Central Banks Women's Data Collector
Coleta dados de mulheres dos bancos centrais das Americas, Europa e Asia

Bancos Centrais:
- Americas: Federal Reserve, BACEN, Banxico, BCRA, BCC, etc
- Europa: ECB, BoE, Bundesbank, Banque de France
- Asia: BOJ, PBOC, RBI, MAS, BOK, etc
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

# Central Banks with Women's Data Sources
CENTRAL_BANKS = {
    # ===========================================
    # AMERICAS
    # ===========================================
    "americas": {
        "FED": {
            "name": "Federal Reserve (USA)",
            "country": "USA",
            "api": "FRED",
            "women_series": {
                "LNS11300002": "Women Labor Force Participation Rate",
                "LNS14000002": "Women Unemployment Rate",
                "LNS12300002": "Women Employment-Population Ratio",
            },
        },
        "BACEN": {
            "name": "Banco Central do Brasil",
            "country": "BRA",
            "api": "BCB SGS",
            "women_series": {
                # BACEN doesn't have direct women series, use World Bank
            },
        },
        "BANXICO": {"name": "Banco de Mexico", "country": "MEX", "api": "SIE", "women_series": {}},
        "BCRA": {"name": "Banco Central de Argentina", "country": "ARG", "api": None, "women_series": {}},
        "BCC": {"name": "Banco Central de Chile", "country": "CHL", "api": None, "women_series": {}},
        "BCRP": {"name": "Banco Central de Peru", "country": "PER", "api": None, "women_series": {}},
        "BCV": {"name": "Banco Central de Venezuela", "country": "VEN", "api": None, "women_series": {}},
        "BCU": {"name": "Banco Central del Uruguay", "country": "URY", "api": None, "women_series": {}},
        "BOC": {"name": "Bank of Canada", "country": "CAN", "api": "Valet", "women_series": {}},
        "BCOL": {"name": "Banco de la Republica (Colombia)", "country": "COL", "api": None, "women_series": {}},
    },
    # ===========================================
    # EUROPE
    # ===========================================
    "europe": {
        "ECB": {"name": "European Central Bank", "country": "EUR", "api": "SDW", "women_series": {}},
        "BOE": {
            "name": "Bank of England",
            "country": "GBR",
            "api": "Statistical Interactive Database",
            "women_series": {},
        },
        "BUNDESBANK": {
            "name": "Deutsche Bundesbank",
            "country": "DEU",
            "api": "Time series databases",
            "women_series": {},
        },
        "BDF": {"name": "Banque de France", "country": "FRA", "api": "Webstat", "women_series": {}},
        "SNB": {"name": "Swiss National Bank", "country": "CHE", "api": "Data Portal", "women_series": {}},
        "RIKSBANK": {"name": "Sveriges Riksbank", "country": "SWE", "api": None, "women_series": {}},
        "NORGES": {"name": "Norges Bank", "country": "NOR", "api": None, "women_series": {}},
        "BDP": {"name": "Banco de Portugal", "country": "PRT", "api": "BPstat", "women_series": {}},
        "BDE": {"name": "Banco de Espana", "country": "ESP", "api": None, "women_series": {}},
        "BDI": {"name": "Banca dItalia", "country": "ITA", "api": None, "women_series": {}},
    },
    # ===========================================
    # ASIA
    # ===========================================
    "asia": {
        "BOJ": {"name": "Bank of Japan", "country": "JPN", "api": "Time-Series Data Search", "women_series": {}},
        "PBOC": {"name": "Peoples Bank of China", "country": "CHN", "api": None, "women_series": {}},
        "RBI": {"name": "Reserve Bank of India", "country": "IND", "api": "DBIE", "women_series": {}},
        "BOK": {"name": "Bank of Korea", "country": "KOR", "api": "ECOS", "women_series": {}},
        "MAS": {"name": "Monetary Authority of Singapore", "country": "SGP", "api": None, "women_series": {}},
        "BOT": {"name": "Bank of Thailand", "country": "THA", "api": None, "women_series": {}},
        "SBV": {"name": "State Bank of Vietnam", "country": "VNM", "api": None, "women_series": {}},
        "BNM": {"name": "Bank Negara Malaysia", "country": "MYS", "api": None, "women_series": {}},
        "BI": {"name": "Bank Indonesia", "country": "IDN", "api": None, "women_series": {}},
        "BSP": {"name": "Bangko Sentral ng Pilipinas", "country": "PHL", "api": None, "women_series": {}},
        "RBA": {"name": "Reserve Bank of Australia", "country": "AUS", "api": "Statistics Tables", "women_series": {}},
        "RBNZ": {"name": "Reserve Bank of New Zealand", "country": "NZL", "api": None, "women_series": {}},
    },
}

# World Bank women's indicators to use as proxy for countries without CB data
WB_WOMEN_INDICATORS = {
    "SL.TLF.CACT.FE.ZS": "Labor force participation rate, female (%)",
    "SL.UEM.TOTL.FE.ZS": "Unemployment, female (%)",
    "SL.EMP.TOTL.SP.FE.ZS": "Employment to population ratio, female (%)",
    "SG.GEN.PARL.ZS": "Seats in parliament held by women (%)",
    "SE.TER.ENRR.FE": "School enrollment, tertiary, female (%)",
}


def get_all_countries():
    """Get all countries from central banks"""
    countries = []
    for region, banks in CENTRAL_BANKS.items():
        for bank_code, bank_info in banks.items():
            if bank_info["country"] != "EUR":
                countries.append(bank_info["country"])
    return list(set(countries))


def fetch_worldbank_women_data(countries: List[str]) -> List[Dict]:
    """Fetch women's data from World Bank for all central bank countries"""

    records = []
    base_url = "https://api.worldbank.org/v2"

    country_str = ";".join(countries)

    for indicator_code, indicator_name in WB_WOMEN_INDICATORS.items():
        url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
        params = {"format": "json", "per_page": 5000, "date": "2010:2024", "source": 2}

        try:
            response = requests.get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if len(data) >= 2 and data[1]:
                    for r in data[1]:
                        r["indicator_code"] = indicator_code
                        r["indicator_name"] = indicator_name
                        records.append(r)
        except Exception as e:
            print(f"    Error fetching {indicator_code}: {e}")
            continue

    return records


def save_to_database(conn, records: List[Dict]) -> int:
    """Save central bank women's data to PostgreSQL"""

    cursor = conn.cursor()

    # Create table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.central_banks_women_data (
            id SERIAL PRIMARY KEY,
            region VARCHAR(20),
            central_bank_code VARCHAR(20),
            central_bank_name VARCHAR(100),
            country_code VARCHAR(10),
            indicator_code VARCHAR(50),
            indicator_name TEXT,
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(100),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(central_bank_code, indicator_code, year)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cb_women_country
        ON sofia.central_banks_women_data(country_code)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cb_women_region
        ON sofia.central_banks_women_data(region)
    """
    )

    # Map countries to central banks
    country_to_bank = {}
    for region, banks in CENTRAL_BANKS.items():
        for bank_code, bank_info in banks.items():
            country_to_bank[bank_info["country"]] = {"code": bank_code, "name": bank_info["name"], "region": region}

    inserted = 0

    for record in records:
        if record.get("value") is None:
            continue

        country = record.get("countryiso3code", record.get("country", {}).get("id", ""))
        if country not in country_to_bank:
            continue

        bank_info = country_to_bank[country]

        try:
            # Normalize country to get country_id
            location = normalize_location(conn, {"country": country})
            country_id = location["country_id"]

            cursor.execute(
                """
                INSERT INTO sofia.central_banks_women_data
                (region, central_bank_code, central_bank_name, country_code, country_id, indicator_code, indicator_name, year, value, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (central_bank_code, indicator_code, year)
                DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            """,
                (
                    bank_info["region"],
                    bank_info["code"],
                    bank_info["name"],
                    country,
                    country_id,
                    record.get("indicator_code", ""),
                    record.get("indicator_name", ""),
                    int(record.get("date")) if record.get("date") else None,
                    float(record.get("value")),
                    "World Bank",
                ),
            )
            inserted += 1
        except:
            continue

    conn.commit()
    cursor.close()
    return inserted


def save_central_banks_info(conn) -> int:
    """Save central banks reference data"""

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.central_banks (
            id SERIAL PRIMARY KEY,
            bank_code VARCHAR(20) NOT NULL,
            bank_name VARCHAR(200),
            country_code VARCHAR(10),
            region VARCHAR(20),
            api_available VARCHAR(100),
            website VARCHAR(200),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bank_code)
        )
    """
    )

    inserted = 0

    for region, banks in CENTRAL_BANKS.items():
        for bank_code, bank_info in banks.items():
            try:
                cursor.execute(
                    """
                    INSERT INTO sofia.central_banks
                    (bank_code, bank_name, country_code, region, api_available)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bank_code)
                    DO UPDATE SET bank_name = EXCLUDED.bank_name
                """,
                    (bank_code, bank_info["name"], bank_info["country"], region, bank_info.get("api", "None")),
                )
                inserted += 1
            except:
                continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("CENTRAL BANKS WOMEN'S DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Central Banks covered:")
    for region, banks in CENTRAL_BANKS.items():
        print(f"  {region.upper()}:")
        for bank_code, bank_info in banks.items():
            print(f"    - {bank_info['name']} ({bank_info['country']})")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    # Save central banks reference
    print("--- CENTRAL BANKS REFERENCE ---")
    print("  Saving central banks info...")
    inserted = save_central_banks_info(conn)
    total_records += inserted
    print(f"    Saved: {inserted} banks")
    print("")

    # Fetch World Bank data for all countries
    print("--- WOMEN'S DATA FROM WORLD BANK ---")
    countries = get_all_countries()
    print(f"  Fetching data for {len(countries)} countries...")

    for indicator_code, indicator_name in WB_WOMEN_INDICATORS.items():
        print(f"  {indicator_name[:50]}...")

    records = fetch_worldbank_women_data(countries)
    if records:
        print(f"    Total fetched: {len(records)} records")
        inserted = save_to_database(conn, records)
        total_records += inserted
        print(f"    Saved: {inserted} records")
    print("")

    conn.close()

    print("=" * 80)
    print("CENTRAL BANKS WOMEN'S DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Regions covered:")
    print("  - Americas: FED, BACEN, Banxico, BCRA, BCC, BOC, etc")
    print("  - Europe: ECB, BoE, Bundesbank, BdF, SNB, etc")
    print("  - Asia: BOJ, PBOC, RBI, MAS, BOK, RBA, etc")
    print("")
    print("Indicators:")
    for code, name in WB_WOMEN_INDICATORS.items():
        print(f"  - {name}")
    print("")
    print("Tables created:")
    print("  - sofia.central_banks (reference)")
    print("  - sofia.central_banks_women_data")


if __name__ == "__main__":
    main()
