#!/usr/bin/env python3
"""
IPEA API Collector - Instituto de Pesquisa Econômica Aplicada
Coleta séries históricas completas (economia, social, infraestrutura)
API: http://ipeadata.gov.br/api/
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

# IPEA Series (selected tech-relevant indicators)
# Full list: http://ipeadata.gov.br/api/odata4/Metadados
IPEA_SERIES = {
    'PRECOS12_IPCAG12': {
        'name': 'IPC-A Geral - Inflação',
        'category': 'inflation',
        'source': 'IBGE'
    },
    'PAN12_PIBPMV12': {
        'name': 'PIB mensal - Valores correntes',
        'category': 'gdp',
        'source': 'IBGE'
    },
    'ESTIMA12_TJOVER12': {
        'name': 'Taxa de juros - Over/Selic',
        'category': 'interest_rate',
        'source': 'BACEN'
    },
    'PAN12_PIBAGRO12': {
        'name': 'PIB Agropecuária',
        'category': 'sector_gdp',
        'source': 'IBGE'
    },
    'PAN12_PIBIND12': {
        'name': 'PIB Indústria',
        'category': 'sector_gdp',
        'source': 'IBGE'
    },
    'PAN12_PIBSERV12': {
        'name': 'PIB Serviços',
        'category': 'sector_gdp',
        'source': 'IBGE'
    },
    'BM12_SALMIN12': {
        'name': 'Salário mínimo',
        'category': 'income',
        'source': 'IPEA'
    },
    'PNADC12_TDESOC12': {
        'name': 'Taxa de desocupação',
        'category': 'employment',
        'source': 'IBGE'
    },
    'PNADC12_RRTH12': {
        'name': 'Rendimento real médio habitual',
        'category': 'income',
        'source': 'IBGE'
    },
    'GAC12_FBCFN12': {
        'name': 'Formação bruta de capital fixo',
        'category': 'investment',
        'source': 'IBGE'
    },
}

def fetch_ipea_series(series_code: str) -> List[Dict[str, Any]]:
    """Fetch data from IPEA API"""

    # IPEA OData API endpoint
    url = f"http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{series_code}')"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Extract values
        values = data.get('value', [])

        print(f"   ✅ Series {series_code}: {len(values)} records")
        return values

    except requests.HTTPError as e:
        print(f"   ❌ HTTP Error for series {series_code}: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error fetching series {series_code}: {e}")
        return []

def save_to_database(conn, series_code: str, series_info: Dict, data: List[Dict]) -> int:
    """Save IPEA data to PostgreSQL"""

    if not data:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.ipea_series (
            id SERIAL PRIMARY KEY,
            series_code VARCHAR(50) NOT NULL,
            series_name TEXT NOT NULL,
            category VARCHAR(50),
            source VARCHAR(50),
            date DATE NOT NULL,
            value DECIMAL(18, 6),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series_code, date)
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ipea_series_code_date
        ON sofia.ipea_series(series_code, date DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ipea_category
        ON sofia.ipea_series(category, date DESC)
    """)

    inserted = 0

    for record in data:
        try:
            # Parse date (format may vary)
            date_str = record.get('VALDATA', '')
            if not date_str:
                continue

            # Extract date part (YYYY-MM-DD)
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()

            # Get value
            value = record.get('VALVALOR')
            if value is None:
                continue

            cursor.execute("""
                INSERT INTO sofia.ipea_series
                (series_code, series_name, category, source, date, value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_code, date)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                series_code,
                series_info['name'],
                series_info['category'],
                series_info['source'],
                date_obj,
                float(value)
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
    print("📊 IPEA API - Instituto de Pesquisa Econômica Aplicada")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: http://ipeadata.gov.br/api/")
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

    print("📊 Fetching IPEA historical series...")
    print("")

    for series_code, series_info in IPEA_SERIES.items():
        print(f"📈 {series_info['name']} ({series_code})")

        # Fetch data
        data = fetch_ipea_series(series_code)

        if data:
            # Save to database
            inserted = save_to_database(conn, series_code, series_info, data)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")

        print("")

    conn.close()

    print("="*80)
    print("✅ IPEA API COLLECTION COMPLETE")
    print("="*80)
    print("")
    print(f"📊 Total series: {len(IPEA_SERIES)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("Series collected:")
    for code, info in IPEA_SERIES.items():
        print(f"  • {info['name']} (source: {info['source']})")
    print("")
    print("💡 Use cases:")
    print("  • Long-term trend analysis (data since 1940s)")
    print("  • Correlate macro indicators with tech sector")
    print("  • Historical comparisons Brazil vs World")
    print("")

if __name__ == '__main__':
    main()
