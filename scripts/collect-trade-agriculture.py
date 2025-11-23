#!/usr/bin/env python3
"""
================================================================================
TRADE & AGRICULTURE DATA COLLECTOR
================================================================================
Sources:
- World Bank (trade indicators)
- UN Data (SDG indicators)
- FAO approximations via World Bank

Tables created:
- sofia.wto_trade_data
- sofia.fao_agriculture_data
- sofia.sdg_indicators
================================================================================
"""

import os
import requests
import psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'sofia'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )

def create_tables(cursor):
    """Create tables if they don't exist"""

    # WTO Trade Data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.wto_trade_data (
            id SERIAL PRIMARY KEY,
            country_code VARCHAR(10),
            country VARCHAR(100),
            indicator_code VARCHAR(50),
            indicator VARCHAR(200),
            value DECIMAL(18, 2),
            year INTEGER,
            source VARCHAR(100) DEFAULT 'World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, indicator_code, year)
        )
    """)

    # FAO Agriculture Data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.fao_agriculture_data (
            id SERIAL PRIMARY KEY,
            country_code VARCHAR(10),
            country VARCHAR(100),
            indicator_code VARCHAR(50),
            indicator VARCHAR(200),
            value DECIMAL(18, 2),
            year INTEGER,
            source VARCHAR(100) DEFAULT 'World Bank/FAO',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, indicator_code, year)
        )
    """)

    # SDG Indicators
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.sdg_indicators (
            id SERIAL PRIMARY KEY,
            country_code VARCHAR(10),
            country VARCHAR(100),
            goal INTEGER,
            indicator_code VARCHAR(50),
            indicator VARCHAR(200),
            value DECIMAL(18, 4),
            year INTEGER,
            source VARCHAR(100) DEFAULT 'World Bank SDG',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, indicator_code, year)
        )
    """)

def fetch_world_bank_indicator(indicator_code, countries="all", per_page=500):
    """Fetch data from World Bank API"""
    url = f"https://api.worldbank.org/v2/country/{countries}/indicator/{indicator_code}"
    params = {
        "format": "json",
        "per_page": per_page,
        "date": "2015:2023"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                return data[1]
    except Exception as e:
        print(f"  ⚠️ Error fetching {indicator_code}: {e}")
    return []

def collect_wto_trade_data(cursor):
    """Collect trade-related indicators"""
    print("\n📊 Collecting WTO/Trade Data...")

    trade_indicators = {
        'NE.EXP.GNFS.ZS': 'Exports of goods and services (% of GDP)',
        'NE.IMP.GNFS.ZS': 'Imports of goods and services (% of GDP)',
        'TG.VAL.TOTL.GD.ZS': 'Merchandise trade (% of GDP)',
        'BX.GSR.GNFS.CD': 'Exports of goods and services (current US$)',
        'BM.GSR.GNFS.CD': 'Imports of goods and services (current US$)',
        'TX.VAL.TECH.MF.ZS': 'High-technology exports (% of manufactured exports)',
    }

    inserted = 0
    for code, name in trade_indicators.items():
        print(f"  Fetching: {name[:50]}...")
        data = fetch_world_bank_indicator(code)

        for item in data:
            if item.get('value') is not None:
                try:
                    cursor.execute("""
                        INSERT INTO sofia.wto_trade_data
                        (country_code, country, indicator_code, indicator, value, year)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (country_code, indicator_code, year) DO UPDATE SET
                        value = EXCLUDED.value, collected_at = CURRENT_TIMESTAMP
                    """, (
                        item['country']['id'],
                        item['country']['value'],
                        code,
                        name,
                        item['value'],
                        int(item['date'])
                    ))
                    inserted += 1
                except Exception as e:
                    pass

    print(f"  ✅ Inserted/Updated: {inserted} trade records")
    return inserted

def collect_fao_agriculture_data(cursor):
    """Collect agriculture-related indicators"""
    print("\n🌾 Collecting FAO/Agriculture Data...")

    agri_indicators = {
        'AG.LND.AGRI.ZS': 'Agricultural land (% of land area)',
        'AG.LND.ARBL.ZS': 'Arable land (% of land area)',
        'AG.YLD.CREL.KG': 'Cereal yield (kg per hectare)',
        'NV.AGR.TOTL.ZS': 'Agriculture, forestry, fishing, value added (% of GDP)',
        'SL.AGR.EMPL.ZS': 'Employment in agriculture (% of total employment)',
        'AG.PRD.FOOD.XD': 'Food production index (2014-2016 = 100)',
        'AG.CON.FERT.ZS': 'Fertilizer consumption (kg per hectare of arable land)',
    }

    inserted = 0
    for code, name in agri_indicators.items():
        print(f"  Fetching: {name[:50]}...")
        data = fetch_world_bank_indicator(code)

        for item in data:
            if item.get('value') is not None:
                try:
                    cursor.execute("""
                        INSERT INTO sofia.fao_agriculture_data
                        (country_code, country, indicator_code, indicator, value, year)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (country_code, indicator_code, year) DO UPDATE SET
                        value = EXCLUDED.value, collected_at = CURRENT_TIMESTAMP
                    """, (
                        item['country']['id'],
                        item['country']['value'],
                        code,
                        name,
                        item['value'],
                        int(item['date'])
                    ))
                    inserted += 1
                except Exception as e:
                    pass

    print(f"  ✅ Inserted/Updated: {inserted} agriculture records")
    return inserted

def collect_sdg_indicators(cursor):
    """Collect SDG-related indicators"""
    print("\n🎯 Collecting SDG Indicators...")

    # SDG indicators mapped to World Bank codes
    sdg_indicators = {
        # SDG 1: No Poverty
        'SI.POV.DDAY': (1, 'Poverty headcount ratio at $2.15/day (%)'),
        # SDG 2: Zero Hunger
        'SN.ITK.DEFC.ZS': (2, 'Prevalence of undernourishment (%)'),
        # SDG 3: Good Health
        'SH.DYN.MORT': (3, 'Mortality rate, under-5 (per 1,000)'),
        'SP.DYN.LE00.IN': (3, 'Life expectancy at birth (years)'),
        # SDG 4: Quality Education
        'SE.PRM.CMPT.ZS': (4, 'Primary completion rate (%)'),
        'SE.ADT.LITR.ZS': (4, 'Literacy rate, adult (%)'),
        # SDG 5: Gender Equality
        'SL.TLF.CACT.FE.ZS': (5, 'Female labor force participation (%)'),
        'SG.GEN.PARL.ZS': (5, 'Women in parliament (%)'),
        # SDG 6: Clean Water
        'SH.H2O.SMDW.ZS': (6, 'Access to safe drinking water (%)'),
        # SDG 7: Affordable Energy
        'EG.ELC.ACCS.ZS': (7, 'Access to electricity (%)'),
        'EG.FEC.RNEW.ZS': (7, 'Renewable energy consumption (%)'),
        # SDG 8: Decent Work
        'SL.UEM.TOTL.ZS': (8, 'Unemployment rate (%)'),
        'NY.GDP.PCAP.CD': (8, 'GDP per capita (current US$)'),
        # SDG 9: Industry/Innovation
        'GB.XPD.RSDV.GD.ZS': (9, 'R&D expenditure (% of GDP)'),
        'IT.NET.USER.ZS': (9, 'Internet users (%)'),
        # SDG 10: Reduced Inequalities
        'SI.POV.GINI': (10, 'Gini index'),
        # SDG 13: Climate Action
        'EN.ATM.CO2E.PC': (13, 'CO2 emissions (metric tons per capita)'),
    }

    inserted = 0
    for code, (goal, name) in sdg_indicators.items():
        print(f"  Fetching SDG {goal}: {name[:40]}...")
        data = fetch_world_bank_indicator(code)

        for item in data:
            if item.get('value') is not None:
                try:
                    cursor.execute("""
                        INSERT INTO sofia.sdg_indicators
                        (country_code, country, goal, indicator_code, indicator, value, year)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (country_code, indicator_code, year) DO UPDATE SET
                        value = EXCLUDED.value, collected_at = CURRENT_TIMESTAMP
                    """, (
                        item['country']['id'],
                        item['country']['value'],
                        goal,
                        code,
                        name,
                        item['value'],
                        int(item['date'])
                    ))
                    inserted += 1
                except Exception as e:
                    pass

    print(f"  ✅ Inserted/Updated: {inserted} SDG records")
    return inserted

def main():
    print("=" * 80)
    print("🌾 TRADE & AGRICULTURE DATA COLLECTOR")
    print("=" * 80)
    print(f"Started: {datetime.now()}")

    conn = get_connection()
    cursor = conn.cursor()

    print("\n📦 Creating tables...")
    create_tables(cursor)
    conn.commit()

    total = 0
    total += collect_wto_trade_data(cursor)
    conn.commit()

    total += collect_fao_agriculture_data(cursor)
    conn.commit()

    total += collect_sdg_indicators(cursor)
    conn.commit()

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print(f"✅ COMPLETED: {total:,} total records")
    print(f"Finished: {datetime.now()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
