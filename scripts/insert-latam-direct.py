#!/usr/bin/env python3
"""
ACLED LATAM Direct Insert - Simplified
Lê temp_latam.xlsx e insere diretamente em acled_aggregated.regional
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, Json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB")
}

def to_snake_case(name: str) -> str:
    return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').strip()

print("="*70)
print("ACLED LATAM Direct Insert")
print("="*70)

# 1. Limpar dados antigos LATAM
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

print("\n🧹 Limpando dados LATAM antigos...")
cur.execute("DELETE FROM acled_aggregated.regional WHERE dataset_slug = 'aggregated-latin-america-caribbean'")
print(f"   Removidos {cur.rowcount:,} registros antigos")

# 2. Ler Excel
print("\n📥 Lendo temp_latam.xlsx...")
df = pd.read_excel("temp_latam.xlsx")
print(f"   Carregados {len(df):,} registros")

# 3. Normalizar colunas
df.columns = [to_snake_case(c) for c in df.columns]
df = df.where(pd.notna(df), None)

print("\n🔄 Preparando registros...")
records = []
for _, row in df.iterrows():
    week_str = None
    year_val = None
    month_val = None
    if row.get('week'):
        try:
            dt = pd.to_datetime(row['week'])
            year_val = int(dt.year)
            month_val = int(dt.month)
            week_str = int(dt.isocalendar().week)
        except:
            pass
            
    metadata = {k: (v.isoformat() if isinstance(v, (pd.Timestamp, datetime)) else v) 
               for k, v in row.items() if k not in ['country', 'events', 'fatalities', 'week', 'year', 'month']}

    records.append((
        'aggregated-latin-america-caribbean',  # dataset_slug
        'Latin America and Caribbean',  # region
        row.get('country'),
        row.get('admin1'),
        row.get('admin2'),
        year_val,
        month_val,
        week_str,
        None,  # date_range_start
        None,  # date_range_end
        float(row['centroid_latitude']) if row.get('centroid_latitude') else None,
        float(row['centroid_longitude']) if row.get('centroid_longitude') else None,
        int(row['events']) if row.get('events') else 0,
        int(row['fatalities']) if row.get('fatalities') else 0,
        row.get('event_type'),
        row.get('disorder_type'),
        Json(metadata),
        'manual_insert',  # source_file_hash
        datetime.now(timezone.utc)
    ))

print(f"   Preparados {len(records):,} registros")

# 4. Inserir SEM ON CONFLICT
print("\n💾 Inserindo em acled_aggregated.regional...")
execute_values(cur, """
    INSERT INTO acled_aggregated.regional (
        dataset_slug, region, country, admin1, admin2, year, month, week, date_range_start, date_range_end,
        centroid_latitude, centroid_longitude, events, fatalities, event_type, disorder_type, metadata,
        source_file_hash, collected_at
    ) VALUES %s
""", records)

print(f"   ✅ Inseridos {len(records):,} registros")

# 5. Verificar
cur.execute("SELECT COUNT(*) FROM acled_aggregated.regional WHERE dataset_slug = 'aggregated-latin-america-caribbean'")
total = cur.fetchone()[0]
print(f"\n📊 Total LATAM em regional: {total:,}")

# 6. Amostra de países
cur.execute("""
    SELECT country, COUNT(*) as cnt
    FROM acled_aggregated.regional
    WHERE dataset_slug = 'aggregated-latin-america-caribbean'
    GROUP BY country
    ORDER BY cnt DESC
    LIMIT 10
""")
print("\n🌎 Top 10 países:")
for country, cnt in cur.fetchall():
    print(f"   {country}: {cnt:,}")

conn.close()
print("\n" + "="*70)
print("✅ LATAM DATA INSERTED")
print("="*70)
