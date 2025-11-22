#!/usr/bin/env python3
"""
MDIC ComexStat API Collector - Comércio Exterior Brasileiro
Coleta dados de importação/exportação por produto, país, estado
API: http://api.comexstat.mdic.gov.br/docs/
"""

import os
import sys
import psycopg2
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'sofia')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'sofia_db'))
}

# Tech-related NCM codes (Brazilian tariff classification)
# NCM 84 = Máquinas, aparelhos e equipamentos
# NCM 85 = Equipamentos elétricos e eletrônicos
TECH_NCM_CODES = {
    '8471': 'Máquinas automáticas de processamento de dados (computadores)',
    '8473': 'Partes e acessórios para máquinas de processamento de dados',
    '8517': 'Aparelhos elétricos para telefonia/telegrafia (smartphones, modems)',
    '8518': 'Microfones, alto-falantes, amplificadores',
    '8523': 'Discos, fitas e outros suportes (pen drives, cartões de memória)',
    '8524': 'Discos, fitas e outros suportes gravados',
    '8525': 'Aparelhos transmissores para radiodifusão',
    '8528': 'Monitores e projetores',
    '8529': 'Partes de aparelhos de transmissão',
    '8534': 'Circuitos impressos',
    '8541': 'Diodos, transistores, semicondutores (chips)',
    '8542': 'Circuitos integrados eletrônicos',
}

def fetch_comexstat_data(ncm_code: str, flow: str, months_back: int = 12) -> List[Dict[str, Any]]:
    """
    Fetch export/import data from ComexStat API

    flow: 'exp' (export) or 'imp' (import)
    """

    # Calculate date range (last N months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)

    # Format as YYYYMM
    start_period = start_date.strftime('%Y%m')
    end_period = end_date.strftime('%Y%m')

    # ComexStat API endpoint
    base_url = "http://api.comexstat.mdic.gov.br/general"

    params = {
        'filter': f'CO_NCM:{ncm_code}',
        'periodType': 'month',
        'periodFrom': start_period,
        'periodTo': end_period,
        'detailLevel': 'COUNTRY'  # Group by country
    }

    url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    try:
        response = requests.get(url, timeout=60)

        # ComexStat may return 404 for no data
        if response.status_code == 404:
            print(f"   ℹ️  No data for NCM {ncm_code} ({flow})")
            return []

        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            print(f"   ✅ NCM {ncm_code} ({flow}): {len(data)} records")
            return data
        else:
            return []

    except requests.HTTPError as e:
        if e.response.status_code != 404:
            print(f"   ❌ HTTP Error for NCM {ncm_code}: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error fetching NCM {ncm_code}: {e}")
        return []

def save_to_database(conn, ncm_code: str, ncm_description: str, flow: str, data: List[Dict]) -> int:
    """Save ComexStat data to PostgreSQL"""

    if not data:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.comexstat_trade (
            id SERIAL PRIMARY KEY,
            flow VARCHAR(10) NOT NULL,
            ncm_code VARCHAR(10) NOT NULL,
            ncm_description TEXT,
            period VARCHAR(6) NOT NULL,
            country_code VARCHAR(10),
            country_name TEXT,
            value_usd DECIMAL(18, 2),
            weight_kg DECIMAL(18, 2),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(flow, ncm_code, period, country_code)
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_comexstat_ncm_period
        ON sofia.comexstat_trade(ncm_code, period DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_comexstat_flow
        ON sofia.comexstat_trade(flow, period DESC)
    """)

    inserted = 0

    for record in data:
        try:
            cursor.execute("""
                INSERT INTO sofia.comexstat_trade
                (flow, ncm_code, ncm_description, period, country_code, country_name, value_usd, weight_kg)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (flow, ncm_code, period, country_code)
                DO UPDATE SET
                    value_usd = EXCLUDED.value_usd,
                    weight_kg = EXCLUDED.weight_kg
            """, (
                flow,
                ncm_code,
                ncm_description,
                record.get('CO_MES', ''),  # Period YYYYMM
                record.get('CO_PAIS', ''),  # Country code
                record.get('NO_PAIS', 'Unknown'),  # Country name
                record.get('VL_FOB', 0),  # Value in USD
                record.get('KG_LIQUIDO', 0)  # Weight in kg
            ))

            inserted += 1

        except Exception as e:
            print(f"   ⚠️  Error inserting record: {e}")
            continue

    conn.commit()
    cursor.close()

    return inserted

def main():
    print("="*80)
    print("📊 MDIC ComexStat API - Comércio Exterior Brasileiro")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: http://api.comexstat.mdic.gov.br/")
    print("")

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print("📊 Fetching tech products trade data (NCM codes)...")
    print("")

    for ncm_code, description in TECH_NCM_CODES.items():
        print(f"📦 {description} (NCM: {ncm_code})")

        # Fetch exports
        export_data = fetch_comexstat_data(ncm_code, 'exp', months_back=12)
        if export_data:
            inserted = save_to_database(conn, ncm_code, description, 'export', export_data)
            total_records += inserted
            print(f"   💾 Exports: {inserted} records")

        # Fetch imports
        import_data = fetch_comexstat_data(ncm_code, 'imp', months_back=12)
        if import_data:
            inserted = save_to_database(conn, ncm_code, description, 'import', import_data)
            total_records += inserted
            print(f"   💾 Imports: {inserted} records")

        print("")

    conn.close()

    print("="*80)
    print("✅ MDIC COMEXSTAT COLLECTION COMPLETE")
    print("="*80)
    print("")
    print(f"📦 Total NCM codes: {len(TECH_NCM_CODES)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("Tech products tracked:")
    for ncm, desc in TECH_NCM_CODES.items():
        print(f"  • {ncm}: {desc}")
    print("")
    print("💡 Use cases:")
    print("  • Correlate chip imports with engineer demand")
    print("  • Track smartphone exports vs local production")
    print("  • Identify growing tech export sectors")
    print("")

if __name__ == '__main__':
    main()
