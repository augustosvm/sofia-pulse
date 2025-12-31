#!/usr/bin/env python3

"""
Sofia Pulse - Socioeconomic Indicators Collector
Collects socioeconomic data for all countries from World Bank API (2015+)
"""

import os
import sys
import time
from typing import Any, Dict, List

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "sofia"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "sofia_db"),
}

# World Bank API - FREE, no key required
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"

# Key socioeconomic and health indicators from World Bank
# Format: (field_name, description, unit)
INDICATORS = {
    # ═══ ECONOMIA - BÁSICO ═══
    "NY.GDP.MKTP.CD": ("gdp_current_usd", "GDP (current US$)", "USD"),
    "NY.GDP.PCAP.CD": ("gdp_per_capita", "GDP per capita (current US$)", "USD"),
    "SP.POP.TOTL": ("population", "Population, total", "people"),
    "SL.UEM.TOTL.ZS": ("unemployment_rate", "Unemployment, total (% of total labor force)", "%"),
    "FP.CPI.TOTL.ZG": ("inflation_rate", "Inflation, consumer prices (annual %)", "%"),
    "SI.POV.GINI": ("gini_index", "Gini index (World Bank estimate)", "index"),
    # ═══ ECONOMIA - FISCAL E MILITAR ═══
    "MS.MIL.XPND.GD.ZS": ("military_expenditure_gdp", "Military expenditure (% of GDP)", "%"),
    "GC.DOD.TOTL.GD.ZS": ("public_debt_gdp", "Central government debt (% of GDP)", "%"),
    "FI.RES.TOTL.CD": ("international_reserves", "Total reserves (USD)", "USD"),
    # ═══ ECONOMIA - COMÉRCIO INTERNACIONAL ═══
    "NE.EXP.GNFS.ZS": ("exports_gdp", "Exports of goods and services (% of GDP)", "%"),
    "NE.IMP.GNFS.ZS": ("imports_gdp", "Imports of goods and services (% of GDP)", "%"),
    "BX.KLT.DINV.CD.WD": ("fdi_inflows", "Foreign direct investment, net inflows (USD)", "USD"),
    # ═══ POBREZA ═══
    "SI.POV.DDAY": ("poverty_extreme", "Poverty headcount ratio at $2.15/day (% of population)", "%"),
    "SI.POV.NAHC": ("poverty_national", "Poverty headcount ratio at national poverty lines (% of population)", "%"),
    # ═══ DEMOGRAFIA ═══
    "SP.DYN.TFRT.IN": ("fertility_rate", "Fertility rate, total (births per woman)", "births/woman"),
    "SH.DYN.NMRT": ("neonatal_mortality_rate", "Neonatal mortality rate (per 1,000 live births)", "per 1000"),
    "SP.URB.TOTL.IN.ZS": ("urban_population", "Urban population (% of total)", "%"),
    "SP.POP.GROW": ("population_growth", "Population growth (annual %)", "%"),
    # ═══ SAÚDE - EXPECTATIVA DE VIDA E MORTALIDADE ═══
    "SP.DYN.LE00.IN": ("life_expectancy", "Life expectancy at birth, total (years)", "years"),
    "SP.DYN.IMRT.IN": ("infant_mortality_rate", "Infant mortality rate (per 1,000 live births)", "per 1000"),
    "SH.STA.MMRT": ("maternal_mortality", "Maternal mortality ratio (per 100,000 live births)", "per 100k"),
    "SP.DYN.CDRT.IN": ("child_mortality_rate", "Under-5 mortality rate (per 1,000 live births)", "per 1000"),
    # ═══ SAÚDE - CAUSAS DE MORTE E DOENÇAS ═══
    "SH.DTH.COMM.ZS": ("communicable_diseases_deaths", "Communicable diseases deaths (% of total)", "%"),
    "SH.DTH.NCOM.ZS": ("noncommunicable_diseases_deaths", "Non-communicable diseases deaths (% of total)", "%"),
    "SH.DTH.INJR.ZS": ("injuries_deaths", "Injury deaths (% of total)", "%"),
    "SH.DYN.AIDS.ZS": ("hiv_prevalence", "HIV prevalence (% of ages 15-49)", "%"),
    "SH.TBS.INCD": ("tuberculosis_incidence", "Tuberculosis incidence (per 100,000)", "per 100k"),
    "SH.STA.SUIC.P5": ("suicide_rate", "Suicide mortality rate (per 100,000)", "per 100k"),
    "SH.PRV.SMOK": ("smoking_prevalence", "Smoking prevalence (% of adults)", "%"),
    # ═══ SAÚDE - RECURSOS ═══
    "SH.MED.PHYS.ZS": ("physicians_per_1000", "Physicians (per 1,000 people)", "per 1000"),
    "SH.MED.BEDS.ZS": ("hospital_beds_per_1000", "Hospital beds (per 1,000 people)", "per 1000"),
    "SH.XPD.CHEX.GD.ZS": ("health_expenditure_gdp", "Health expenditure (% of GDP)", "%"),
    "SH.XPD.CHEX.PC.CD": ("health_expenditure_per_capita", "Health expenditure per capita (USD)", "USD"),
    "SH.IMM.IDPT": ("immunization_dpt", "DPT immunization (% of children)", "%"),
    "SH.IMM.MEAS": ("immunization_measles", "Measles immunization (% of children)", "%"),
    # ═══ EDUCAÇÃO ═══
    "SE.ADT.LITR.ZS": ("literacy_rate", "Literacy rate (% of ages 15+)", "%"),
    "SE.XPD.TOTL.GD.ZS": ("education_expenditure_gdp", "Education expenditure (% of GDP)", "%"),
    "SE.PRM.ENRR": ("school_enrollment_primary", "Primary school enrollment (% gross)", "%"),
    "SE.SEC.ENRR": ("school_enrollment_secondary", "Secondary school enrollment (% gross)", "%"),
    "SE.TER.ENRR": ("school_enrollment_tertiary", "Tertiary school enrollment (% gross)", "%"),
    "SE.PRM.CMPT.ZS": ("primary_completion_rate", "Primary completion rate (%)", "%"),
    "SE.SEC.CMPT.LO.ZS": ("lower_secondary_completion", "Lower secondary completion (%)", "%"),
    # ═══ MEIO AMBIENTE E CLIMA ═══
    "EN.ATM.CO2E.PC": ("co2_emissions_per_capita", "CO2 emissions per capita (tons)", "tons"),
    "EN.ATM.GHGT.KT.CE": ("greenhouse_gas_emissions", "Greenhouse gas emissions (kt CO2eq)", "kt CO2eq"),
    "EG.USE.ELEC.KH.PC": ("electricity_consumption_per_capita", "Electricity consumption per capita (kWh)", "kWh"),
    "EG.ELC.RNEW.ZS": ("renewable_electricity", "Renewable electricity (% of total)", "%"),
    "AG.LND.FRST.ZS": ("forest_area", "Forest area (% of land)", "%"),
    "EN.ATM.PM25.MC.M3": ("air_pollution_pm25", "PM2.5 air pollution (µg/m³)", "µg/m³"),
    # ═══ TECNOLOGIA E CONECTIVIDADE ═══
    "IT.NET.USER.ZS": ("internet_users", "Internet users (% of population)", "%"),
    "IT.CEL.SETS.P2": ("mobile_subscriptions", "Mobile subscriptions (per 100)", "per 100"),
    "IT.NET.BBND.P2": ("broadband_subscriptions", "Fixed broadband subscriptions (per 100)", "per 100"),
    # ═══ INOVAÇÃO E P&D ═══
    "GB.XPD.RSDV.GD.ZS": ("research_development_gdp", "Research & development expenditure (% of GDP)", "%"),
    # ═══ INFRAESTRUTURA E ACESSO ═══
    "IS.ROD.PAVE.ZS": ("paved_roads", "Paved roads (% of total)", "%"),
    "EG.ELC.ACCS.ZS": ("electricity_access", "Access to electricity (% of pop)", "%"),
    "SH.H2O.SMDW.ZS": ("improved_water_source", "Safe drinking water (% of pop)", "%"),
    "SH.STA.SMSS.ZS": ("improved_sanitation", "Safe sanitation (% of pop)", "%"),
}


def fetch_indicator_data(indicator_code: str, start_year: int = 2015) -> List[Dict[str, Any]]:
    """Fetch data for a specific indicator from World Bank API"""

    print(f"   Fetching {indicator_code}...", end=" ")

    all_data = []
    page = 1
    per_page = 1000

    try:
        while True:
            url = f"{WORLD_BANK_BASE_URL}/{indicator_code}"
            params = {
                "format": "json",
                "per_page": per_page,
                "page": page,
                "date": f"{start_year}:2024",  # 2015 to 2024
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # World Bank returns [metadata, data]
            if len(data) < 2 or not data[1]:
                break

            all_data.extend(data[1])

            # Check if there are more pages
            metadata = data[0]
            total_pages = metadata.get("pages", 1)

            if page >= total_pages:
                break

            page += 1
            time.sleep(0.1)  # Be nice to the API

        print(f"✅ {len(all_data)} records")
        return all_data

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   ⚠️  World Bank API now requires subscription key (changed 2025)")
        print(f"   💡 This collector is temporarily disabled until API key is obtained")
        print(f"   📖 See CLAUDE.md for details and alternatives")
        return []


def process_world_bank_data(raw_data: List[Dict], indicator_code: str) -> List[Dict[str, Any]]:
    """Process raw World Bank data into our format"""

    indicator_info = INDICATORS.get(indicator_code)
    if not indicator_info:
        return []

    field_name, description, unit = indicator_info

    records = []
    for item in raw_data:
        if item.get("value") is None:
            continue

        records.append(
            {
                "country_code": item.get("countryiso3code"),
                "country_name": (
                    item.get("country", {}).get("value")
                    if isinstance(item.get("country"), dict)
                    else item.get("country")
                ),
                "year": int(item.get("date", 0)),
                "indicator_code": indicator_code,
                "indicator_name": field_name,
                "value": float(item["value"]),
                "unit": unit,
            }
        )

    return records


def safe_float(value, max_value=999999999999.99):
    """Safely convert to float, handling None"""
    if value is None:
        return None
    try:
        float_val = float(value)
        if abs(float_val) > max_value:
            return None
        return float_val
    except (ValueError, TypeError):
        return None


def safe_int(value, max_value=9223372036854775807):
    """Safely convert to int, handling None"""
    if value is None:
        return None
    try:
        int_val = int(value)
        if abs(int_val) > max_value:
            return None
        return int_val
    except (ValueError, OverflowError):
        return None


def insert_to_db(records: List[Dict[str, Any]]) -> int:
    """Insert socioeconomic data to PostgreSQL"""

    if not records:
        print("⚠️  No records to insert")
        return 0

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO sofia.socioeconomic_indicators
            (country_code, country_name, year, indicator_code, indicator_name,
             value, unit, data_source, collected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (country_code, year, indicator_code)
            DO UPDATE SET
                value = EXCLUDED.value,
                unit = EXCLUDED.unit,
                data_source = EXCLUDED.data_source,
                updated_at = CURRENT_TIMESTAMP
        """

        batch_data = []
        for record in records:
            batch_data.append(
                (
                    record.get("country_code"),
                    record.get("country_name"),
                    safe_int(record.get("year")),
                    record.get("indicator_code"),
                    record.get("indicator_name"),
                    safe_float(record.get("value")),
                    record.get("unit"),
                    "World Bank",
                )
            )

        execute_batch(cur, insert_query, batch_data, page_size=500)
        conn.commit()

        print(f"✅ Inserted/updated {len(batch_data)} records")
        return len(batch_data)

    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        import traceback

        traceback.print_exc()
        return 0
    finally:
        if conn:
            conn.close()


def main():
    print("=" * 80)
    print("🌍 SOCIOECONOMIC & HEALTH INDICATORS COLLECTOR")
    print("=" * 80)
    print()

    print(f"📊 Collecting {len(INDICATORS)} indicators from World Bank (2015-2024)")
    print()
    print("Categories:")
    print("   💰 Economy - Basic (6 indicators)")
    print("   🏦 Economy - Fiscal & Military (3 indicators)")
    print("   🌐 Economy - International Trade (3 indicators)")
    print("   🏚️  Poverty (2 indicators)")
    print("   👨‍👩‍👧‍👦 Demographics (4 indicators)")
    print("   ❤️  Health - Mortality (4 indicators)")
    print("   🏥 Health - Diseases (7 indicators)")
    print("   💉 Health - Resources (6 indicators)")
    print("   📚 Education (7 indicators)")
    print("   🌍 Environment & Climate (6 indicators)")
    print("   📱 Technology & Connectivity (3 indicators)")
    print("   🔬 Innovation & R&D (1 indicator)")
    print("   🏗️  Infrastructure (4 indicators)")
    print()

    all_records = []

    for indicator_code, (field_name, description, unit) in INDICATORS.items():
        print(f"📈 {description}")

        # Fetch data from World Bank
        raw_data = fetch_indicator_data(indicator_code, start_year=2015)

        if raw_data:
            # Process into our format
            processed = process_world_bank_data(raw_data, indicator_code)
            all_records.extend(processed)
            print(f"   ✅ Processed {len(processed)} valid records")

        print()

    if not all_records:
        print("❌ No data fetched")
        sys.exit(1)

    # Insert to database
    print("💾 Inserting to database...")
    inserted = insert_to_db(all_records)

    # Show summary
    print()
    print("📊 Summary:")
    print(f"   Total indicators: {len(INDICATORS)}")
    print(f"   Total records: {len(all_records)}")
    print(f"   Inserted/updated: {inserted}")

    # Show sample by indicator
    print()
    print("📈 Records by indicator:")
    indicator_counts = {}
    for record in all_records:
        indicator = record["indicator_name"]
        indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1

    for indicator, count in sorted(indicator_counts.items()):
        print(f"   {indicator}: {count}")

    print()
    print("=" * 80)
    print(f"✅ COMPLETE - Inserted {inserted} records")
    print("=" * 80)
    print()
    print("💡 Data covers 2015-2024 for all countries")
    print("   Source: World Bank Open Data (api.worldbank.org)")


if __name__ == "__main__":
    main()
