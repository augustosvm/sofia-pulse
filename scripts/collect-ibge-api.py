#!/usr/bin/env python3
"""
IBGE SIDRA API Collector - Instituto Brasileiro de Geografia e Estatística
Coleta dados oficiais: PIB, inflação, emprego, produção, demografia

API SIDRA: https://apisidra.ibge.gov.br/
Documentação: https://apisidra.ibge.gov.br/home/ajuda
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

# IBGE Agregados (indicators)
# Ref: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
IBGE_INDICATORS = {
    '1737': {
        'name': 'PIB - Produto Interno Bruto',
        'category': 'economy',
        'frequency': 'trimestral',
        'unit': 'R$ milhões'
    },
    '6381': {
        'name': 'IPCA - Inflação (mensal)',
        'category': 'inflation',
        'frequency': 'mensal',
        'unit': '%'
    },
    '6784': {
        'name': 'PNAD Contínua - Taxa de desemprego',
        'category': 'employment',
        'frequency': 'trimestral',
        'unit': '%'
    },
    '6385': {
        'name': 'PIM-PF - Produção Industrial',
        'category': 'production',
        'frequency': 'mensal',
        'unit': 'índice'
    },
    '6786': {
        'name': 'PNAD Contínua - Rendimento médio',
        'category': 'income',
        'frequency': 'trimestral',
        'unit': 'R$'
    },
    '8419': {
        'name': 'Pesquisa Pulso Empresa - Impacto COVID',
        'category': 'business',
        'frequency': 'quinzenal',
        'unit': '%'
    },
}

def fetch_ibge_sidra(table_code: str, indicator_info: Dict) -> List[Dict]:
    """Fetch data from IBGE SIDRA API

    API SIDRA: https://apisidra.ibge.gov.br/
    Format: /values/t/{tabela}/n{nivel}/{territorios}/p/{periodos}/v/{variaveis}
    """

    # SIDRA API base URL - for actual data extraction
    base_url = "https://apisidra.ibge.gov.br/values"

    # Build URL:
    # t = table code
    # n1 = Brazil level, all = all territories at that level
    # p = periods: last 12 or "all" for all, or specific like "202301"
    # v = variables: "all" or specific variable codes

    # Use "last 12" format for periods (most recent 12 periods)
    url = f"{base_url}/t/{table_code}/n1/all/p/last%2012/v/all"

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Sofia-Pulse-Collector/1.0'
        }
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        # SIDRA returns list with first row being headers
        if data and len(data) > 1:
            print(f"   ✅ Table {table_code}: {len(data)-1} records fetched")
            return data
        else:
            print(f"   ⚠️  Table {table_code}: No data returned")
            return []

    except requests.HTTPError as e:
        # Try with fewer periods
        print(f"   ⚠️  HTTP Error {e.response.status_code}, trying with fewer periods...")
        try:
            alt_url = f"{base_url}/t/{table_code}/n1/all/p/last%206/v/all"
            response = requests.get(alt_url, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 1:
                print(f"   ✅ Table {table_code}: {len(data)-1} records fetched (6 periods)")
                return data
            return []
        except Exception as alt_e:
            print(f"   ❌ HTTP Error for table {table_code}: {e}")
            return []
    except Exception as e:
        print(f"   ❌ Error fetching table {table_code}: {e}")
        return []

def parse_ibge_sidra_data(table_code: str, indicator_info: Dict, raw_data: List[Dict]) -> List[Dict]:
    """Parse IBGE SIDRA API response into structured records

    SIDRA API returns data as a list where:
    - First element (index 0) contains column headers
    - Remaining elements contain data rows
    """

    records = []

    if not raw_data or len(raw_data) < 2:
        return records

    try:
        # First row is header
        headers = raw_data[0]

        # Find key columns
        header_keys = list(headers.keys()) if isinstance(headers, dict) else []

        # Data rows start from index 1
        for row in raw_data[1:]:
            if not isinstance(row, dict):
                continue

            # Get value (usually in 'V' key)
            value = row.get('V', '')
            if not value or value in ['...', '-', 'X', '']:
                continue

            try:
                value_float = float(value.replace(',', '.'))
            except ValueError:
                continue

            # Get period (usually in 'D2C' or similar key for trimestre/mes)
            period = row.get('D2C', row.get('D3C', row.get('D4C', '')))
            if not period:
                # Try to find any key with period-like value
                for key in row.keys():
                    if key.startswith('D') and 'C' in key:
                        period = row.get(key, '')
                        if period:
                            break

            # Get territorial info
            territorial_code = row.get('D1C', '1')  # 1 = Brasil
            territorial_name = row.get('D1N', 'Brasil')

            # Get variable name
            variable_name = row.get('D3N', row.get('D2N', indicator_info['name']))

            records.append({
                'agregado_id': table_code,
                'indicator_name': indicator_info['name'],
                'category': indicator_info['category'],
                'unit': indicator_info['unit'],
                'frequency': indicator_info['frequency'],
                'localidade_id': territorial_code,
                'localidade_nome': territorial_name,
                'period': period,
                'value': value_float,
                'variable_name': variable_name
            })

    except Exception as e:
        print(f"   ⚠️  Error parsing data: {e}")

    return records

def save_to_database(conn, records: List[Dict]) -> int:
    """Save IBGE data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.ibge_indicators (
            id SERIAL PRIMARY KEY,
            agregado_id VARCHAR(20) NOT NULL,
            indicator_name TEXT NOT NULL,
            category VARCHAR(50),
            unit VARCHAR(50),
            frequency VARCHAR(20),
            localidade_id VARCHAR(20),
            localidade_nome TEXT,
            period VARCHAR(20) NOT NULL,
            value DECIMAL(18, 6),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(agregado_id, localidade_id, period)
        )
    """)

    # Create index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ibge_agregado_period
        ON sofia.ibge_indicators(agregado_id, period DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ibge_category
        ON sofia.ibge_indicators(category, period DESC)
    """)

    inserted = 0

    for record in records:
        try:
            cursor.execute("""
                INSERT INTO sofia.ibge_indicators
                (agregado_id, indicator_name, category, unit, frequency,
                 localidade_id, localidade_nome, period, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (agregado_id, localidade_id, period)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                record['agregado_id'],
                record['indicator_name'],
                record['category'],
                record['unit'],
                record['frequency'],
                record['localidade_id'],
                record['localidade_nome'],
                record['period'],
                record['value']
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
    print("📊 IBGE SIDRA API - Instituto Brasileiro de Geografia e Estatística")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://apisidra.ibge.gov.br/")
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

    print("📊 Fetching IBGE indicators...")
    print("")

    for table_code, indicator_info in IBGE_INDICATORS.items():
        print(f"📈 {indicator_info['name']} (Table: {table_code})")

        # Fetch data from SIDRA API (last 12 periods)
        raw_data = fetch_ibge_sidra(table_code, indicator_info)

        if raw_data:
            # Parse SIDRA format data
            records = parse_ibge_sidra_data(table_code, indicator_info, raw_data)
            print(f"   📋 Parsed: {len(records)} records")

            if records:
                # Save to database
                inserted = save_to_database(conn, records)
                total_records += inserted
                print(f"   💾 Saved: {inserted} records")

        print("")

    conn.close()

    print("="*80)
    print("✅ IBGE API COLLECTION COMPLETE")
    print("="*80)
    print("")
    print(f"📊 Total indicators: {len(IBGE_INDICATORS)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("Indicators collected:")
    for agregado_id, info in IBGE_INDICATORS.items():
        print(f"  • {info['name']} ({info['frequency']})")
    print("")

if __name__ == '__main__':
    main()
