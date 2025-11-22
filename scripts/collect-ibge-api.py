#!/usr/bin/env python3
"""
IBGE API Collector - Instituto Brasileiro de Geografia e Estatística
Coleta dados oficiais: PIB, inflação, emprego, produção, demografia
API: https://servicodados.ibge.gov.br/api/docs
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

def fetch_ibge_agregado(agregado_id: str) -> Dict[str, Any]:
    """Fetch data from IBGE Agregados API"""

    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{agregado_id}/periodos/-12/variaveis/allxallxall"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        print(f"   ✅ Agregado {agregado_id}: fetched")
        return data

    except requests.HTTPError as e:
        print(f"   ❌ HTTP Error for agregado {agregado_id}: {e}")
        return {}
    except Exception as e:
        print(f"   ❌ Error fetching agregado {agregado_id}: {e}")
        return {}

def parse_ibge_data(agregado_id: str, indicator_info: Dict, raw_data: List[Dict]) -> List[Dict]:
    """Parse IBGE API response into structured records"""

    records = []

    if not raw_data:
        return records

    try:
        for item in raw_data:
            if 'resultados' not in item:
                continue

            for resultado in item['resultados']:
                if 'series' not in resultado:
                    continue

                for serie in resultado['series']:
                    localidade = serie.get('localidade', {})
                    localidade_id = localidade.get('id', 'BR')
                    localidade_nome = localidade.get('nome', 'Brasil')

                    # Get time series data
                    series_data = serie.get('serie', {})

                    for period, value in series_data.items():
                        if value and value != '...':
                            try:
                                records.append({
                                    'agregado_id': agregado_id,
                                    'indicator_name': indicator_info['name'],
                                    'category': indicator_info['category'],
                                    'unit': indicator_info['unit'],
                                    'frequency': indicator_info['frequency'],
                                    'localidade_id': localidade_id,
                                    'localidade_nome': localidade_nome,
                                    'period': period,
                                    'value': float(value)
                                })
                            except ValueError:
                                continue

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
    print("📊 IBGE API - Instituto Brasileiro de Geografia e Estatística")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://servicodados.ibge.gov.br/api/")
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

    for agregado_id, indicator_info in IBGE_INDICATORS.items():
        print(f"📈 {indicator_info['name']} (ID: {agregado_id})")

        # Fetch data (last 12 periods)
        raw_data = fetch_ibge_agregado(agregado_id)

        if raw_data:
            # Parse data
            records = parse_ibge_data(agregado_id, indicator_info, raw_data)
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
