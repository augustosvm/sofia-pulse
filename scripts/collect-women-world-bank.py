#!/usr/bin/env python3
"""
Comprehensive Women & Gender Data Collector - World Bank
Coleta dados extensivos sobre mulheres de todas as fontes do World Bank

APIs:
- World Bank Gender Data Portal: https://genderdata.worldbank.org/
- World Bank Open Data API: https://api.worldbank.org/v2/
"""

import os
import sys
import psycopg2
import requests
from datetime import datetime
from typing import List, Dict, Any

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'sofia')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'sofia_db'))
}

# Comprehensive Women/Gender Indicators from World Bank
WOMEN_INDICATORS = {
    # ===========================================
    # LABOR & EMPLOYMENT
    # ===========================================
    'SL.TLF.CACT.FE.ZS': 'Labor force participation rate, female (% ages 15+)',
    'SL.TLF.CACT.MA.ZS': 'Labor force participation rate, male (% ages 15+)',
    'SL.TLF.CACT.FM.ZS': 'Labor force participation rate ratio (female/male)',
    'SL.EMP.TOTL.SP.FE.ZS': 'Employment to population ratio, female (%)',
    'SL.EMP.TOTL.SP.MA.ZS': 'Employment to population ratio, male (%)',
    'SL.UEM.TOTL.FE.ZS': 'Unemployment rate, female (%)',
    'SL.UEM.TOTL.MA.ZS': 'Unemployment rate, male (%)',
    'SL.UEM.1524.FE.ZS': 'Youth unemployment rate, female (% ages 15-24)',
    'SL.UEM.1524.MA.ZS': 'Youth unemployment rate, male (% ages 15-24)',
    'SL.EMP.SELF.FE.ZS': 'Self-employed, female (% of female employment)',
    'SL.EMP.VULN.FE.ZS': 'Vulnerable employment, female (%)',
    'SL.EMP.WORK.FE.ZS': 'Wage and salaried workers, female (%)',

    # Employment by sector
    'SL.AGR.EMPL.FE.ZS': 'Employment in agriculture, female (%)',
    'SL.IND.EMPL.FE.ZS': 'Employment in industry, female (%)',
    'SL.SRV.EMPL.FE.ZS': 'Employment in services, female (%)',

    # ===========================================
    # EDUCATION
    # ===========================================
    'SE.PRM.ENRR.FE': 'School enrollment, primary, female (% gross)',
    'SE.SEC.ENRR.FE': 'School enrollment, secondary, female (% gross)',
    'SE.TER.ENRR.FE': 'School enrollment, tertiary, female (% gross)',
    'SE.ENR.PRIM.FM.ZS': 'School enrollment, primary (gender parity index)',
    'SE.ENR.SECO.FM.ZS': 'School enrollment, secondary (gender parity index)',
    'SE.ENR.TERT.FM.ZS': 'School enrollment, tertiary (gender parity index)',
    'SE.ADT.LITR.FE.ZS': 'Literacy rate, adult female (%)',
    'SE.ADT.LITR.MA.ZS': 'Literacy rate, adult male (%)',
    'SE.ADT.1524.LT.FE.ZS': 'Literacy rate, youth female (% ages 15-24)',
    'SE.PRM.CMPT.FE.ZS': 'Primary completion rate, female (%)',
    'SE.SEC.CMPT.LO.FE.ZS': 'Lower secondary completion rate, female (%)',

    # STEM Education
    'SE.TER.GRAD.FE.SI.ZS': 'Female graduates from Science programs (%)',

    # ===========================================
    # POLITICAL PARTICIPATION
    # ===========================================
    'SG.GEN.PARL.ZS': 'Proportion of seats held by women in national parliaments (%)',
    'SG.GEN.MNST.ZS': 'Proportion of women in ministerial level positions (%)',
    'SG.GEN.LSOM.ZS': 'Proportion of women in senior & middle management (%)',

    # ===========================================
    # HEALTH & REPRODUCTIVE
    # ===========================================
    'SP.DYN.LE00.FE.IN': 'Life expectancy at birth, female (years)',
    'SP.DYN.LE00.MA.IN': 'Life expectancy at birth, male (years)',
    'SH.STA.MMRT': 'Maternal mortality ratio (per 100,000 live births)',
    'SP.ADO.TFRT': 'Adolescent fertility rate (births per 1,000 women ages 15-19)',
    'SP.DYN.TFRT.IN': 'Total fertility rate (births per woman)',
    'SP.DYN.CONU.ZS': 'Contraceptive prevalence (%)',
    'SH.STA.ANVC.ZS': 'Pregnant women receiving prenatal care (%)',
    'SH.STA.BRTC.ZS': 'Births attended by skilled health staff (%)',
    'SH.HIV.1524.FE.ZS': 'HIV prevalence, female (% ages 15-24)',
    'SH.HIV.1524.MA.ZS': 'HIV prevalence, male (% ages 15-24)',

    # ===========================================
    # ECONOMIC OPPORTUNITY
    # ===========================================
    'IC.FRM.FEMO.ZS': 'Firms with female top manager (%)',
    'IC.FRM.FEMM.ZS': 'Firms with female participation in ownership (%)',
    'SG.OWN.HSOK.FE.ZS': 'Women who own a house alone (%)',
    'SG.OWN.LDOK.FE.ZS': 'Women who own land alone (%)',
    'FX.OWN.TOTL.FE.ZS': 'Account ownership, female (% age 15+)',
    'FX.OWN.TOTL.MA.ZS': 'Account ownership, male (% age 15+)',

    # ===========================================
    # VIOLENCE & SAFETY
    # ===========================================
    'SG.VAW.1549.ZS': 'Women who experienced violence (% ever-partnered women)',
    'SG.VAW.IPVS.ZS': 'Intimate partner violence prevalence (%)',
    'SG.VAW.ARGU.ZS': 'Women who believe husband is justified to beat wife (%)',

    # ===========================================
    # LEGAL RIGHTS (Women, Business and the Law)
    # ===========================================
    'SG.LAW.INDX': 'Women Business and the Law Index Score',
    'SG.LAW.INDX.MO': 'Women Business and the Law: Mobility score',
    'SG.LAW.INDX.WP': 'Women Business and the Law: Workplace score',
    'SG.LAW.INDX.PY': 'Women Business and the Law: Pay score',
    'SG.LAW.INDX.MR': 'Women Business and the Law: Marriage score',
    'SG.LAW.INDX.PR': 'Women Business and the Law: Parenthood score',
    'SG.LAW.INDX.EN': 'Women Business and the Law: Entrepreneurship score',
    'SG.LAW.INDX.AS': 'Women Business and the Law: Assets score',
    'SG.LAW.INDX.PN': 'Women Business and the Law: Pension score',

    # ===========================================
    # POPULATION & DEMOGRAPHICS
    # ===========================================
    'SP.POP.TOTL.FE.ZS': 'Population, female (% of total)',
    'SP.POP.65UP.FE.ZS': 'Population ages 65+, female (%)',
    'SP.POP.0014.FE.ZS': 'Population ages 0-14, female (%)',
    'SP.POP.1564.FE.ZS': 'Population ages 15-64, female (%)',
}

# Countries to collect data from (expanded list)
COUNTRIES = [
    # Americas
    'BRA', 'USA', 'CAN', 'MEX', 'ARG', 'CHL', 'COL', 'PER', 'VEN', 'ECU',
    'BOL', 'PRY', 'URY', 'CRI', 'PAN', 'DOM', 'GTM', 'HND', 'SLV', 'NIC',
    # Europe
    'DEU', 'FRA', 'GBR', 'ITA', 'ESP', 'PRT', 'NLD', 'BEL', 'SWE', 'NOR',
    'DNK', 'FIN', 'AUT', 'CHE', 'POL', 'CZE', 'HUN', 'ROU', 'GRC', 'IRL',
    # Asia
    'CHN', 'JPN', 'KOR', 'IND', 'IDN', 'THA', 'VNM', 'MYS', 'SGP', 'PHL',
    'PAK', 'BGD', 'TWN', 'HKG', 'ARE', 'SAU', 'ISR', 'TUR', 'IRN', 'IRQ',
    # Africa
    'ZAF', 'NGA', 'EGY', 'KEN', 'ETH', 'GHA', 'TZA', 'UGA', 'MAR', 'DZA',
    # Oceania
    'AUS', 'NZL',
    # Russia
    'RUS',
]


def fetch_indicator_data(indicator_code: str) -> List[Dict]:
    """Fetch indicator data from World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    country_str = ';'.join(COUNTRIES)

    url = f"{base_url}/country/{country_str}/indicator/{indicator_code}"
    params = {
        'format': 'json',
        'per_page': 5000,
        'date': '2000:2024',
        'source': 2
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception as e:
        print(f"   Error: {e}")
        return []


def save_to_database(conn, records: List[Dict], indicator_code: str, indicator_name: str) -> int:
    """Save women/gender indicator data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.women_world_bank_data (
            id SERIAL PRIMARY KEY,
            indicator_code VARCHAR(50) NOT NULL,
            indicator_name TEXT,
            indicator_category VARCHAR(50),
            country_code VARCHAR(3),
            country_name VARCHAR(100),
            year INTEGER,
            value DECIMAL(18, 6),
            source VARCHAR(50) DEFAULT 'World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_code, country_code, year)
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_women_wb_indicator_year
        ON sofia.women_world_bank_data(indicator_code, year DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_women_wb_country
        ON sofia.women_world_bank_data(country_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_women_wb_category
        ON sofia.women_world_bank_data(indicator_category)
    """)

    # Determine category based on indicator code
    category = 'other'
    if indicator_code.startswith('SL.'):
        category = 'labor'
    elif indicator_code.startswith('SE.'):
        category = 'education'
    elif indicator_code.startswith('SG.GEN.PARL') or indicator_code.startswith('SG.GEN.MNST'):
        category = 'political'
    elif indicator_code.startswith('SP.') or indicator_code.startswith('SH.'):
        category = 'health'
    elif indicator_code.startswith('IC.') or indicator_code.startswith('FX.') or 'OWN' in indicator_code:
        category = 'economic'
    elif 'VAW' in indicator_code:
        category = 'violence'
    elif indicator_code.startswith('SG.LAW'):
        category = 'legal'

    inserted = 0

    for record in records:
        if record.get('value') is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO sofia.women_world_bank_data
                (indicator_code, indicator_name, indicator_category, country_code, country_name, year, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (indicator_code, country_code, year)
                DO UPDATE SET value = EXCLUDED.value, indicator_category = EXCLUDED.indicator_category
            """, (
                indicator_code,
                indicator_name,
                category,
                record.get('countryiso3code', record.get('country', {}).get('id')),
                record.get('country', {}).get('value'),
                int(record.get('date')) if record.get('date') else None,
                float(record.get('value'))
            ))
            inserted += 1
        except Exception as e:
            continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("COMPREHENSIVE WOMEN & GENDER DATA - WORLD BANK")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: World Bank Gender Data Portal")
    print(f"API: https://api.worldbank.org/v2/")
    print("")
    print(f"Indicators: {len(WOMEN_INDICATORS)}")
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
    successful = 0
    failed = 0

    # Group indicators by category for display
    categories = {
        'Labor & Employment': [k for k in WOMEN_INDICATORS if k.startswith('SL.')],
        'Education': [k for k in WOMEN_INDICATORS if k.startswith('SE.')],
        'Political': [k for k in WOMEN_INDICATORS if 'PARL' in k or 'MNST' in k or 'LSOM' in k],
        'Health': [k for k in WOMEN_INDICATORS if k.startswith('SP.') or k.startswith('SH.')],
        'Economic': [k for k in WOMEN_INDICATORS if k.startswith('IC.') or k.startswith('FX.') or 'OWN' in k],
        'Violence': [k for k in WOMEN_INDICATORS if 'VAW' in k],
        'Legal': [k for k in WOMEN_INDICATORS if k.startswith('SG.LAW')],
    }

    for cat_name, indicators in categories.items():
        if not indicators:
            continue
        print(f"--- {cat_name} ---")
        for indicator_code in indicators:
            indicator_name = WOMEN_INDICATORS[indicator_code]
            print(f"  {indicator_name[:60]}...")

            records = fetch_indicator_data(indicator_code)

            if records:
                print(f"    Fetched: {len(records)} records")
                inserted = save_to_database(conn, records, indicator_code, indicator_name)
                total_records += inserted
                successful += 1
                print(f"    Saved: {inserted} records")
            else:
                failed += 1
                print(f"    No data")
        print("")

    conn.close()

    print("=" * 80)
    print("WORLD BANK WOMEN DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful indicators: {successful}")
    print(f"Failed indicators: {failed}")
    print("")
    print("Categories covered:")
    print("  - Labor & Employment (participation, unemployment, sectors)")
    print("  - Education (enrollment, literacy, STEM)")
    print("  - Political Participation (parliament, ministers)")
    print("  - Health & Reproductive (maternal, fertility, HIV)")
    print("  - Economic Opportunity (firms, ownership, accounts)")
    print("  - Violence Against Women (prevalence, attitudes)")
    print("  - Legal Rights (Women Business and Law Index)")


if __name__ == '__main__':
    main()
