#!/usr/bin/env python3
"""
BACEN SGS API Collector - Banco Central do Brasil
Coleta indicadores macroeconômicos (Selic, Câmbio, IPCA, PIB)
API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json
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

# BACEN SGS Series
# Ref: https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries
BACEN_SERIES = {
    '432': {
        'name': 'Selic - Taxa de juros',
        'unit': '%',
        'frequency': 'daily',
        'category': 'monetary_policy'
    },
    '433': {
        'name': 'IPCA - Inflação',
        'unit': '%',
        'frequency': 'monthly',
        'category': 'inflation'
    },
    '1': {
        'name': 'Dólar - Taxa de câmbio (comercial)',
        'unit': 'BRL/USD',
        'frequency': 'daily',
        'category': 'exchange_rate'
    },
    '4189': {
        'name': 'PIB mensal',
        'unit': 'R$ milhões',
        'frequency': 'monthly',
        'category': 'gdp'
    },
    '11': {
        'name': 'IGP-M - Inflação geral',
        'unit': '%',
        'frequency': 'monthly',
        'category': 'inflation'
    },
    '4390': {
        'name': 'Taxa de desemprego',
        'unit': '%',
        'frequency': 'monthly',
        'category': 'employment'
    },
    '13522': {
        'name': 'Reservas internacionais',
        'unit': 'US$ milhões',
        'frequency': 'daily',
        'category': 'reserves'
    },
}

def fetch_bacen_series(series_code: str, days_back: int = 365) -> List[Dict[str, Any]]:
    """Fetch data from BACEN SGS API"""

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Format dates as DD/MM/YYYY
    start_str = start_date.strftime('%d/%m/%Y')
    end_str = end_date.strftime('%d/%m/%Y')

    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados?formato=json&dataInicial={start_str}&dataFinal={end_str}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        print(f"   ✅ Series {series_code}: {len(data)} records")
        return data

    except requests.HTTPError as e:
        print(f"   ❌ HTTP Error for series {series_code}: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error fetching series {series_code}: {e}")
        return []

def save_to_database(conn, series_code: str, series_info: Dict, data: List[Dict]):
    """Save BACEN data to PostgreSQL"""

    if not data:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.bacen_sgs_series (
            id SERIAL PRIMARY KEY,
            series_code VARCHAR(10) NOT NULL,
            series_name TEXT NOT NULL,
            category VARCHAR(50),
            unit VARCHAR(50),
            frequency VARCHAR(20),
            date DATE NOT NULL,
            value DECIMAL(18, 6),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series_code, date)
        )
    """)

    # Create index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bacen_series_code_date
        ON sofia.bacen_sgs_series(series_code, date DESC)
    """)

    inserted = 0

    for record in data:
        try:
            # Parse date (DD/MM/YYYY)
            date_str = record['data']
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()

            # Parse value
            value = float(record['valor'])

            cursor.execute("""
                INSERT INTO sofia.bacen_sgs_series
                (series_code, series_name, category, unit, frequency, date, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_code, date)
                DO UPDATE SET value = EXCLUDED.value
            """, (
                series_code,
                series_info['name'],
                series_info['category'],
                series_info['unit'],
                series_info['frequency'],
                date_obj,
                value
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
    print("📊 BACEN SGS API - Banco Central do Brasil")
    print("="*80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://api.bcb.gov.br/dados/serie/")
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

    print("📊 Fetching BACEN series...")
    print("")

    for series_code, series_info in BACEN_SERIES.items():
        print(f"📈 {series_info['name']} (code: {series_code})")

        # Fetch data (last 365 days)
        data = fetch_bacen_series(series_code, days_back=365)

        if data:
            # Save to database
            inserted = save_to_database(conn, series_code, series_info, data)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")

        print("")

    conn.close()

    print("="*80)
    print("✅ BACEN SGS COLLECTION COMPLETE")
    print("="*80)
    print("")
    print(f"📊 Total series: {len(BACEN_SERIES)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("Series collected:")
    for code, info in BACEN_SERIES.items():
        print(f"  • {code}: {info['name']} ({info['frequency']})")
    print("")
    print("💡 Use cases:")
    print("  • Correlate Selic with startup funding")
    print("  • Track Dollar exchange rate vs foreign tech investment")
    print("  • Analyze inflation (IPCA) vs tech salary adjustments")
    print("")

if __name__ == '__main__':
    main()
