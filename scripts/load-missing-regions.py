#!/usr/bin/env python3
"""Load missing ACLED regions directly to security_events"""

import os, psycopg2, pandas as pd, hashlib
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', '91.98.158.19'),
    port=5432,
    user=os.getenv('POSTGRES_USER', 'dbs_sofia'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB', 'sofia')
)

MISSING_REGIONS = [
    {'region': 'Latin America', 'file': 'data/acled/raw/aggregated-latin-america-caribbean/2026-01-15/Latin-America-the-Caribbean_aggregated_data_up_to-2026-01-03.xlsx'},
    {'region': 'Middle East', 'file': 'data/acled/raw/aggregated-middle-east/2026-01-15/Middle-East_aggregated_data_up_to-2026-01-03.xlsx'},
    {'region': 'Asia Pacific', 'file': 'data/acled/raw/aggregated-asia-pacific/2026-01-15/Asia-Pacific_aggregated_data_up_to-2026-01-03.xlsx'},
    {'region': 'Africa', 'file': 'data/acled/raw/aggregated-africa/2026-01-15/Africa_aggregated_data_up_to-2026-01-03.xlsx'}
]

def load_region(region_info):
    file_path = region_info['file']
    region_name = region_info['region']

    print(f"\nLoading {region_name}...")
    df = pd.read_excel(file_path)
    print(f"  Read {len(df):,} rows")

    # Normalize columns
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]

    # Extract date components
    df['week_date'] = pd.to_datetime(df['week'])
    df['year'] = df['week_date'].dt.year
    df['month'] = df['week_date'].dt.month

    # Filter: must have geo
    df = df[df['centroid_latitude'].notna() & df['centroid_longitude'].notna()]
    print(f"  With geo: {len(df):,} rows")

    # Bulk insert
    cursor = conn.cursor()
    inserted = 0
    batch_size = 5000

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        values = []

        for _, row in batch.iterrows():
            # Generate source_id
            key = f"acled_{region_name}_{row['country']}_{row['year']}_{row['month']}_{row['centroid_latitude']}_{row['centroid_longitude']}"
            source_id = hashlib.md5(key.encode()).hexdigest()

            # Event date
            event_date = f"{row['year']}-{row['month']:02d}-01"

            values.append((
                'ACLED',
                source_id,
                event_date,
                row['country'],
                None,
                float(row['centroid_latitude']),
                float(row['centroid_longitude']),
                row.get('event_type', 'Unknown'),
                int(row.get('fatalities', 0)),
                None
            ))

        if values:
            from psycopg2.extras import execute_values
            execute_values(cursor, """
                INSERT INTO sofia.security_events
                (source, source_id, event_date, country_name, country_code,
                 latitude, longitude, event_type, fatalities, raw_payload)
                VALUES %s
                ON CONFLICT (source, source_id) DO NOTHING
            """, values)
            conn.commit()
            inserted += len(values)
            print(f"  Inserted {inserted:,}/{len(df):,}...")

    cursor.close()
    print(f"  ✅ Done: {inserted:,} records")
    return inserted

total = 0
for region in MISSING_REGIONS:
    try:
        total += load_region(region)
    except Exception as e:
        print(f"  ❌ Error: {e}")

print(f"\n{'='*60}")
print(f"Total inserted: {total:,}")
print(f"{'='*60}")

conn.close()
