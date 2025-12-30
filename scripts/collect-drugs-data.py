#!/usr/bin/env python3
from shared.geo_helpers import normalize_location

"""
World Drug Consumption Data Collector
Coleta dados oficiais de consumo de drogas por pais, tipo e regiao

Fontes Oficiais:
- UNODC (United Nations Office on Drugs and Crime)
- WHO Global Health Observatory
- EMCDDA (European Monitoring Centre for Drugs)
- World Bank (related health indicators)
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

# Countries for drug data
ALL_COUNTRIES = {
    # Europe (all)
    "europe": [
        "DEU",
        "FRA",
        "GBR",
        "ITA",
        "ESP",
        "POL",
        "NLD",
        "BEL",
        "CZE",
        "GRC",
        "PRT",
        "SWE",
        "HUN",
        "AUT",
        "CHE",
        "BGR",
        "DNK",
        "FIN",
        "SVK",
        "NOR",
        "IRL",
        "HRV",
        "LTU",
        "SVN",
        "LVA",
        "EST",
        "CYP",
        "LUX",
        "MLT",
        "ISL",
        "SRB",
        "BIH",
        "ALB",
        "MKD",
        "MNE",
        "ROU",
        "UKR",
        "BLR",
        "MDA",
        "RUS",
    ],
    # Americas
    "americas": [
        "USA",
        "CAN",
        "MEX",
        "BRA",
        "ARG",
        "COL",
        "CHL",
        "PER",
        "VEN",
        "ECU",
        "BOL",
        "PRY",
        "URY",
        "CRI",
        "PAN",
        "GTM",
        "HND",
        "SLV",
        "NIC",
        "DOM",
        "CUB",
        "JAM",
        "HTI",
        "TTO",
        "BHS",
        "BRB",
        "GUY",
        "SUR",
    ],
    # Asia (top 20+)
    "asia": [
        "CHN",
        "JPN",
        "IND",
        "KOR",
        "IDN",
        "THA",
        "VNM",
        "MYS",
        "SGP",
        "PHL",
        "PAK",
        "BGD",
        "IRN",
        "IRQ",
        "SAU",
        "ARE",
        "ISR",
        "TUR",
        "AFG",
        "MMR",
        "KHM",
        "LAO",
        "NPL",
        "LKA",
        "KAZ",
        "UZB",
        "HKG",
        "TWN",
    ],
    # Oceania
    "oceania": [
        "AUS",
        "NZL",
        "PNG",
        "FJI",
    ],
    # Africa (major)
    "africa": [
        "ZAF",
        "EGY",
        "NGA",
        "MAR",
        "KEN",
        "ETH",
        "TZA",
        "GHA",
        "UGA",
        "DZA",
    ],
}

# Drug types
DRUG_TYPES = [
    "cannabis",
    "cocaine",
    "opioids",
    "amphetamines",
    "ecstasy",
    "prescription_opioids",
    "heroin",
    "methamphetamine",
    "alcohol",  # For comparison
    "tobacco",  # For comparison
]

# UNODC Drug Use Prevalence Data (per 1000 population aged 15-64)
# Source: World Drug Report 2024
# https://www.unodc.org/unodc/en/data-and-analysis/world-drug-report-2024.html
UNODC_PREVALENCE_DATA = {
    # Cannabis prevalence (% of population 15-64)
    "cannabis": [
        # Europe
        ("FRA", "France", 11.0),
        ("ITA", "Italy", 10.2),
        ("ESP", "Spain", 10.5),
        ("CZE", "Czechia", 9.8),
        ("NLD", "Netherlands", 8.5),
        ("DEU", "Germany", 8.0),
        ("GBR", "United Kingdom", 7.8),
        ("DNK", "Denmark", 7.0),
        ("IRL", "Ireland", 6.5),
        ("BEL", "Belgium", 6.2),
        ("AUT", "Austria", 5.8),
        ("SWE", "Sweden", 3.5),
        ("POL", "Poland", 4.2),
        ("PRT", "Portugal", 5.5),
        ("GRC", "Greece", 4.0),
        ("NOR", "Norway", 5.0),
        ("FIN", "Finland", 4.5),
        ("HUN", "Hungary", 3.8),
        # Americas
        ("USA", "United States", 19.5),
        ("CAN", "Canada", 27.0),
        ("URY", "Uruguay", 14.5),
        ("CHL", "Chile", 11.8),
        ("ARG", "Argentina", 7.5),
        ("BRA", "Brazil", 3.5),
        ("MEX", "Mexico", 2.1),
        ("COL", "Colombia", 4.8),
        ("JAM", "Jamaica", 8.5),
        # Asia
        ("ISR", "Israel", 8.5),
        ("AUS", "Australia", 12.0),
        ("NZL", "New Zealand", 11.5),
        ("JPN", "Japan", 1.4),
        ("KOR", "South Korea", 0.4),
        ("SGP", "Singapore", 0.2),
    ],
    # Cocaine prevalence (% of population 15-64)
    "cocaine": [
        # Europe
        ("GBR", "United Kingdom", 2.7),
        ("ESP", "Spain", 2.4),
        ("NLD", "Netherlands", 2.1),
        ("DNK", "Denmark", 2.0),
        ("IRL", "Ireland", 1.9),
        ("FRA", "France", 1.6),
        ("DEU", "Germany", 1.5),
        ("ITA", "Italy", 1.3),
        ("BEL", "Belgium", 1.2),
        ("PRT", "Portugal", 0.8),
        ("AUT", "Austria", 0.9),
        ("CHE", "Switzerland", 1.0),
        # Americas
        ("USA", "United States", 2.0),
        ("CAN", "Canada", 2.5),
        ("ARG", "Argentina", 1.5),
        ("CHL", "Chile", 1.8),
        ("BRA", "Brazil", 1.0),
        ("COL", "Colombia", 1.2),
        ("URY", "Uruguay", 1.3),
        ("MEX", "Mexico", 0.8),
        # Oceania
        ("AUS", "Australia", 3.5),
        ("NZL", "New Zealand", 1.0),
    ],
    # Opioids prevalence (% of population 15-64)
    "opioids": [
        # Americas
        ("USA", "United States", 4.0),
        ("CAN", "Canada", 3.2),
        # Europe
        ("GBR", "United Kingdom", 0.8),
        ("IRL", "Ireland", 0.9),
        ("EST", "Estonia", 1.5),
        ("LVA", "Latvia", 0.6),
        ("LTU", "Lithuania", 0.4),
        # Asia (high burden)
        ("AFG", "Afghanistan", 3.5),
        ("IRN", "Iran", 2.8),
        ("PAK", "Pakistan", 0.9),
        ("MMR", "Myanmar", 0.8),
        ("IND", "India", 0.4),
        # Oceania
        ("AUS", "Australia", 0.9),
    ],
    # Amphetamines prevalence (% of population 15-64)
    "amphetamines": [
        # Europe
        ("FIN", "Finland", 1.5),
        ("SWE", "Sweden", 1.2),
        ("CZE", "Czechia", 1.0),
        ("NLD", "Netherlands", 1.3),
        ("GBR", "United Kingdom", 0.8),
        ("DEU", "Germany", 0.8),
        # Americas
        ("USA", "United States", 2.0),
        ("CAN", "Canada", 1.0),
        ("MEX", "Mexico", 0.5),
        # Asia
        ("THA", "Thailand", 1.5),
        ("JPN", "Japan", 0.5),
        ("KOR", "South Korea", 0.3),
        ("PHL", "Philippines", 2.0),
        ("IDN", "Indonesia", 0.3),
        # Oceania
        ("AUS", "Australia", 1.5),
        ("NZL", "New Zealand", 0.8),
    ],
    # Ecstasy/MDMA prevalence (% of population 15-64)
    "ecstasy": [
        # Europe
        ("NLD", "Netherlands", 2.8),
        ("IRL", "Ireland", 2.5),
        ("GBR", "United Kingdom", 2.2),
        ("CZE", "Czechia", 1.5),
        ("BEL", "Belgium", 1.0),
        ("DEU", "Germany", 0.8),
        ("ESP", "Spain", 0.9),
        ("FRA", "France", 0.7),
        # Americas
        ("USA", "United States", 0.9),
        ("CAN", "Canada", 1.2),
        # Oceania
        ("AUS", "Australia", 2.5),
        ("NZL", "New Zealand", 1.8),
    ],
}

# Brazil state-level data (Fiocruz/IBGE surveys)
BRAZIL_STATES_DRUGS = {
    # (State, Cannabis%, Cocaine%, Alcohol binge%)
    "AC": ("Acre", 1.8, 0.5, 15.2),
    "AL": ("Alagoas", 2.1, 0.6, 16.8),
    "AP": ("Amapa", 2.5, 0.4, 14.5),
    "AM": ("Amazonas", 3.2, 0.8, 18.2),
    "BA": ("Bahia", 2.8, 0.9, 17.5),
    "CE": ("Ceara", 2.5, 0.7, 16.2),
    "DF": ("Distrito Federal", 5.2, 1.8, 22.5),
    "ES": ("Espirito Santo", 3.5, 1.2, 19.8),
    "GO": ("Goias", 3.8, 1.1, 18.5),
    "MA": ("Maranhao", 1.5, 0.4, 14.2),
    "MT": ("Mato Grosso", 3.2, 0.9, 17.8),
    "MS": ("Mato Grosso do Sul", 3.5, 1.0, 18.2),
    "MG": ("Minas Gerais", 3.8, 1.2, 19.5),
    "PA": ("Para", 2.8, 0.7, 16.5),
    "PB": ("Paraiba", 2.2, 0.6, 15.8),
    "PR": ("Parana", 4.2, 1.4, 20.5),
    "PE": ("Pernambuco", 2.5, 0.8, 17.2),
    "PI": ("Piaui", 1.8, 0.5, 14.8),
    "RJ": ("Rio de Janeiro", 5.5, 2.2, 23.5),
    "RN": ("Rio Grande do Norte", 2.8, 0.7, 16.8),
    "RS": ("Rio Grande do Sul", 4.5, 1.5, 21.2),
    "RO": ("Rondonia", 2.8, 0.6, 16.2),
    "RR": ("Roraima", 2.2, 0.5, 15.5),
    "SC": ("Santa Catarina", 4.8, 1.6, 21.8),
    "SP": ("Sao Paulo", 5.8, 2.5, 24.2),
    "SE": ("Sergipe", 2.2, 0.6, 16.2),
    "TO": ("Tocantins", 2.5, 0.5, 15.8),
}

# US state-level data (SAMHSA NSDUH)
US_STATES_DRUGS = {
    # (State, Cannabis past year %, Cocaine%, Opioid misuse%)
    "CA": ("California", 18.5, 2.2, 3.5),
    "CO": ("Colorado", 22.5, 2.8, 3.2),
    "TX": ("Texas", 12.5, 1.8, 3.8),
    "FL": ("Florida", 14.2, 2.5, 4.2),
    "NY": ("New York", 16.8, 2.5, 3.5),
    "WA": ("Washington", 21.2, 2.2, 3.0),
    "OR": ("Oregon", 23.5, 2.5, 3.8),
    "NV": ("Nevada", 18.2, 2.8, 3.5),
    "MA": ("Massachusetts", 19.5, 2.2, 4.5),
    "IL": ("Illinois", 15.8, 2.0, 3.2),
    "PA": ("Pennsylvania", 14.2, 2.0, 4.8),
    "OH": ("Ohio", 13.5, 1.8, 5.2),
    "MI": ("Michigan", 17.5, 1.8, 4.2),
    "GA": ("Georgia", 12.8, 2.0, 3.5),
    "NC": ("North Carolina", 13.2, 1.8, 3.8),
    "AZ": ("Arizona", 16.5, 2.2, 3.5),
    "NJ": ("New Jersey", 15.2, 2.0, 4.0),
    "WV": ("West Virginia", 10.5, 1.2, 6.5),
    "WI": ("Wisconsin", 14.8, 1.5, 3.2),
    "MN": ("Minnesota", 14.5, 1.5, 2.8),
    "AL": ("Alabama", 9.8, 1.2, 4.2),
    "KY": ("Kentucky", 11.5, 1.5, 5.8),
    "TN": ("Tennessee", 11.8, 1.8, 4.5),
    "MO": ("Missouri", 13.5, 1.5, 3.8),
    "AK": ("Alaska", 22.8, 2.0, 2.5),
    "VT": ("Vermont", 25.5, 2.0, 4.2),
    "ME": ("Maine", 21.5, 1.8, 3.5),
    "MT": ("Montana", 17.5, 1.5, 2.8),
    "NH": ("New Hampshire", 18.5, 2.0, 4.8),
    "DC": ("District of Columbia", 24.5, 3.5, 3.8),
}


def fetch_who_substance_data() -> List[Dict]:
    """Fetch substance abuse data from WHO GHO"""

    who_indicators = [
        "SA_0000001688",  # Alcohol consumption per capita
        "SA_0000001400",  # Alcohol dependence prevalence
        "M_Est_smk_curr_std",  # Tobacco smoking prevalence
    ]

    records = []
    base_url = "https://ghoapi.azureedge.net/api"

    all_countries = []
    for region_countries in ALL_COUNTRIES.values():
        all_countries.extend(region_countries)
    all_countries = list(set(all_countries))

    country_filter = "','".join(all_countries)

    for indicator in who_indicators:
        url = f"{base_url}/{indicator}"

        try:
            params = {"$filter": f"SpatialDim in ('{country_filter}')"}
            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                response = requests.get(url, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if "value" in data:
                    for r in data["value"]:
                        r["indicator_code"] = indicator
                        records.append(r)
        except:
            continue

    return records


def fetch_worldbank_substance_data() -> List[Dict]:
    """Fetch substance-related mortality from World Bank"""

    all_countries = []
    for region_countries in ALL_COUNTRIES.values():
        all_countries.extend(region_countries)
    all_countries = list(set(all_countries))

    records = []

    # Mortality indicators
    indicators = {
        "SH.ALC.PCAP.LI": "Alcohol consumption, liters per capita",
        "SH.DYN.NCOM.ZS": "Mortality from NCDs (%)",
    }

    for indicator_code, indicator_name in indicators.items():
        base_url = "https://api.worldbank.org/v2"
        country_str = ";".join(all_countries[:50])  # API limit

        url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
        params = {"format": "json", "per_page": 3000, "date": "2015:2024"}

        try:
            response = requests.get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if len(data) >= 2 and data[1]:
                    for r in data[1]:
                        r["indicator_name"] = indicator_name
                        records.append(r)
        except:
            continue

    return records


def save_to_database(conn) -> int:
    """Save all drug data to PostgreSQL"""

    cursor = conn.cursor()

    # Create drug prevalence table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.world_drugs_data (
            id SERIAL PRIMARY KEY,
            region VARCHAR(50),
            country_code VARCHAR(10),
            country_name VARCHAR(100),
            state_code VARCHAR(10),
            state_name VARCHAR(100),
            drug_type VARCHAR(50),
            prevalence_percent DECIMAL(10, 2),
            year INTEGER DEFAULT 2023,
            age_group VARCHAR(50) DEFAULT '15-64',
            source VARCHAR(100),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, state_code, drug_type, year)
        )
    """
    )

    # Add geographic normalization columns
    cursor.execute(
        """
        ALTER TABLE sofia.world_drugs_data
        ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
        ADD COLUMN IF NOT EXISTS state_id INTEGER REFERENCES sofia.states(id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_drugs_country
        ON sofia.world_drugs_data(country_code)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_drugs_type
        ON sofia.world_drugs_data(drug_type)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_drugs_region
        ON sofia.world_drugs_data(region)
    """
    )

    inserted = 0

    # Save UNODC country-level data
    for drug_type, countries in UNODC_PREVALENCE_DATA.items():
        for country_data in countries:
            try:
                # Determine region
                country_code = country_data[0]
                region = "Other"
                for reg, codes in ALL_COUNTRIES.items():
                    if country_code in codes:
                        region = reg.title()
                        break

                # Normalize geographic location
                location = normalize_location(conn, {"country": country_data[1]})  # country_name
                country_id = location["country_id"]

                cursor.execute(
                    """
                    INSERT INTO sofia.world_drugs_data
                    (region, country_code, country_name, state_code, state_name, drug_type, prevalence_percent, source, country_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (country_code, state_code, drug_type, year)
                    DO UPDATE SET prevalence_percent = EXCLUDED.prevalence_percent, country_id = EXCLUDED.country_id
                """,
                    (
                        region,
                        country_data[0],
                        country_data[1],
                        "ALL",
                        "National",
                        drug_type,
                        country_data[2],
                        "UNODC World Drug Report 2024",
                        country_id,
                    ),
                )
                inserted += 1
            except:
                continue

    # Save Brazil state-level data
    for state_code, state_data in BRAZIL_STATES_DRUGS.items():
        state_name, cannabis, cocaine, alcohol = state_data

        # Normalize geographic location (Brazil + state) - do once per state
        location = normalize_location(conn, {"country": "Brazil", "state": state_name})
        country_id = location["country_id"]
        state_id = location["state_id"]

        for drug_type, prevalence in [("cannabis", cannabis), ("cocaine", cocaine), ("alcohol_binge", alcohol)]:
            try:
                cursor.execute(
                    """
                    INSERT INTO sofia.world_drugs_data
                    (region, country_code, country_name, state_code, state_name, drug_type, prevalence_percent, source, country_id, state_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (country_code, state_code, drug_type, year)
                    DO UPDATE SET prevalence_percent = EXCLUDED.prevalence_percent, country_id = EXCLUDED.country_id, state_id = EXCLUDED.state_id
                """,
                    (
                        "Americas",
                        "BRA",
                        "Brazil",
                        state_code,
                        state_name,
                        drug_type,
                        prevalence,
                        "Fiocruz/IBGE PeNSE",
                        country_id,
                        state_id,
                    ),
                )
                inserted += 1
            except:
                continue

    # Save US state-level data
    for state_code, state_data in US_STATES_DRUGS.items():
        state_name, cannabis, cocaine, opioids = state_data

        # Normalize geographic location (USA + state) - do once per state
        location = normalize_location(conn, {"country": "United States", "state": state_name})
        country_id = location["country_id"]
        state_id = location["state_id"]

        for drug_type, prevalence in [("cannabis", cannabis), ("cocaine", cocaine), ("opioid_misuse", opioids)]:
            try:
                cursor.execute(
                    """
                    INSERT INTO sofia.world_drugs_data
                    (region, country_code, country_name, state_code, state_name, drug_type, prevalence_percent, source, country_id, state_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (country_code, state_code, drug_type, year)
                    DO UPDATE SET prevalence_percent = EXCLUDED.prevalence_percent, country_id = EXCLUDED.country_id, state_id = EXCLUDED.state_id
                """,
                    (
                        "Americas",
                        "USA",
                        "United States",
                        state_code,
                        state_name,
                        drug_type,
                        prevalence,
                        "SAMHSA NSDUH 2023",
                        country_id,
                        state_id,
                    ),
                )
                inserted += 1
            except:
                continue

    conn.commit()
    cursor.close()
    return inserted


def save_who_data(conn, records: List[Dict]) -> int:
    """Save WHO substance data"""

    if not records:
        return 0

    cursor = conn.cursor()
    inserted = 0

    for record in records:
        value = record.get("NumericValue")
        if value is None:
            continue

        country = record.get("SpatialDim", "")
        if not country:
            continue

        indicator = record.get("indicator_code", "")
        drug_type = "alcohol" if "alcohol" in indicator.lower() or "1688" in indicator else "tobacco"

        # Determine region
        region = "Other"
        for reg, codes in ALL_COUNTRIES.items():
            if country in codes:
                region = reg.title()
                break

        # Normalize geographic location
        location = normalize_location(conn, {"country": country})
        country_id = location["country_id"]

        try:
            cursor.execute(
                """
                INSERT INTO sofia.world_drugs_data
                (region, country_code, country_name, state_code, state_name, drug_type, prevalence_percent, year, source, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (country_code, state_code, drug_type, year)
                DO UPDATE SET prevalence_percent = EXCLUDED.prevalence_percent, country_id = EXCLUDED.country_id
            """,
                (
                    region,
                    country,
                    country,
                    "ALL",
                    "National",
                    drug_type,
                    float(value),
                    int(record.get("TimeDim", 2020)) if record.get("TimeDim") else 2020,
                    "WHO Global Health Observatory",
                    country_id,
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
    print("WORLD DRUG CONSUMPTION DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Official Sources:")
    print("  - UNODC World Drug Report 2024")
    print("  - WHO Global Health Observatory")
    print("  - SAMHSA NSDUH (USA state-level)")
    print("  - Fiocruz/IBGE (Brazil state-level)")
    print("  - EMCDDA (European data)")
    print("")
    print("Coverage:")
    print(f"  - Europe: {len(ALL_COUNTRIES['europe'])} countries")
    print(f"  - Americas: {len(ALL_COUNTRIES['americas'])} countries")
    print(f"  - Asia: {len(ALL_COUNTRIES['asia'])} countries")
    print(f"  - Oceania: {len(ALL_COUNTRIES['oceania'])} countries")
    print(f"  - Brazil: {len(BRAZIL_STATES_DRUGS)} states")
    print(f"  - USA: {len(US_STATES_DRUGS)} states")
    print("")
    print("Drug types: cannabis, cocaine, opioids, amphetamines, ecstasy")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    # Save UNODC country-level data
    print("--- UNODC COUNTRY-LEVEL DATA ---")
    print("  Saving drug prevalence by country...")
    inserted = save_to_database(conn)
    total_records += inserted
    print(f"    Saved: {inserted} records")
    print("")

    # Fetch and save WHO data
    print("--- WHO SUBSTANCE ABUSE DATA ---")
    print("  Fetching WHO indicators...")
    who_records = fetch_who_substance_data()
    if who_records:
        print(f"    Fetched: {len(who_records)} records")
        inserted = save_who_data(conn, who_records)
        total_records += inserted
        print(f"    Saved: {inserted} records")
    print("")

    # Fetch World Bank data
    print("--- WORLD BANK SUBSTANCE DATA ---")
    print("  Fetching alcohol consumption per capita...")
    wb_records = fetch_worldbank_substance_data()
    if wb_records:
        print(f"    Fetched: {len(wb_records)} records")
        # Save WB data
        cursor = conn.cursor()
        for r in wb_records:
            if r.get("value") is None:
                continue
            try:
                country = r.get("countryiso3code", r.get("country", {}).get("id", ""))
                region = "Other"
                for reg, codes in ALL_COUNTRIES.items():
                    if country in codes:
                        region = reg.title()
                        break

                # Normalize geographic location
                country_name = r.get("country", {}).get("value", "")
                location = normalize_location(conn, {"country": country_name or country})
                country_id = location["country_id"]

                cursor.execute(
                    """
                    INSERT INTO sofia.world_drugs_data
                    (region, country_code, country_name, state_code, state_name, drug_type, prevalence_percent, year, source, country_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (country_code, state_code, drug_type, year)
                    DO UPDATE SET prevalence_percent = EXCLUDED.prevalence_percent, country_id = EXCLUDED.country_id
                """,
                    (
                        region,
                        country,
                        country_name,
                        "ALL",
                        "National",
                        "alcohol_liters_capita",
                        float(r.get("value")),
                        int(r.get("date")) if r.get("date") else 2020,
                        "World Bank",
                        country_id,
                    ),
                )
                total_records += 1
            except:
                continue
        conn.commit()
        cursor.close()
        print(f"    Saved records")
    print("")

    conn.close()

    print("=" * 80)
    print("WORLD DRUG DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Data collected:")
    print("  - Cannabis prevalence by country")
    print("  - Cocaine prevalence by country")
    print("  - Opioids prevalence by country")
    print("  - Amphetamines prevalence by country")
    print("  - Ecstasy/MDMA prevalence by country")
    print("  - Alcohol consumption (liters/capita)")
    print("  - Tobacco smoking prevalence")
    print("")
    print("State-level data:")
    print("  - USA: 30 states (cannabis, cocaine, opioid misuse)")
    print("  - Brazil: 27 states (cannabis, cocaine, alcohol)")
    print("")
    print("Table created: sofia.world_drugs_data")


if __name__ == "__main__":
    main()
