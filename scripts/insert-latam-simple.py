#!/usr/bin/env python3
"""
ACLED LATAM Ultra-Simplified Insert
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    dbname=os.getenv("POSTGRES_DB")
)
conn.autocommit = True
cur = conn.cursor()

print("ACLED LATAM Insert - Ultra Simplified")

# Limpar antigos
cur.execute("DELETE FROM acled_aggregated.regional WHERE dataset_slug = 'aggregated-latin-america-caribbean'")
print(f"Removed {cur.rowcount} old records")

# Ler Excel
df = pd.read_excel("temp_latam.xlsx")
print(f"Loaded {len(df):,} records")

# Preparar apenas campos essenciais
records = []
for _, row in df.iterrows():
    try:
        records.append((
            'aggregated-latin-america-caribbean',
            'Latin America and Caribbean',
            str(row.get('Country', '')),
            None,  # admin1
            None,  # admin2
            None,  # year
            None,  # month
            None,  # week
            None,  # date_range_start
            None,  # date_range_end
            float(row['Centroid Latitude']) if pd.notna(row.get('Centroid Latitude')) else None,
            float(row['Centroid Longitude']) if pd.notna(row.get('Centroid Longitude')) else None,
            int(row['Events']) if pd.notna(row.get('Events')) else 0,
            int(row['Fatalities']) if pd.notna(row.get('Fatalities')) else 0,
            None,  # event_type
            None,  # disorder_type
            None,  # metadata
            'manual',
            datetime.now(timezone.utc)
        ))
    except Exception as e:
        continue

print(f"Prepared {len(records):,} records")

# Inserir
execute_values(cur, """
    INSERT INTO acled_aggregated.regional (
        dataset_slug, region, country, admin1, admin2, year, month, week, date_range_start, date_range_end,
        centroid_latitude, centroid_longitude, events, fatalities, event_type, disorder_type, metadata,
        source_file_hash, collected_at
    ) VALUES %s
""", records)

print(f"✅ Inserted {len(records):,} records")

# Verificar
cur.execute("SELECT COUNT(*) FROM acled_aggregated.regional WHERE dataset_slug = 'aggregated-latin-america-caribbean'")
print(f"Total LATAM: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT country, COUNT(*) FROM acled_aggregated.regional
    WHERE dataset_slug = 'aggregated-latin-america-caribbean'
    GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10
""")
print("\nTop countries:")
for c, cnt in cur.fetchall():
    print(f"  {c}: {cnt:,}")

conn.close()
