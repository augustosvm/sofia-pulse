#!/usr/bin/env python3
"""
ACLED LATAM → security_events (Batch Insert with NaN Sanitization)
Bypasses acled_aggregated.regional and inserts directly into sofia.security_events
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, Json
import hashlib
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB")
}

BATCH_SIZE = 5000
XLSX_PATH = "temp_latam.xlsx"

def sanitize_value(val):
    """Convert NaN/Infinity to None for Postgres"""
    if pd.isna(val) or val in [float('inf'), float('-inf')]:
        return None
    return val

def main():
    print("="*70)
    print("ACLED LATAM → security_events (Batch Insert)")
    print("="*70)
    
    # 1. Read XLSX
    print(f"\n📥 Reading {XLSX_PATH}...")
    df = pd.read_excel(XLSX_PATH)
    print(f"   Loaded {len(df):,} rows")
    
    # 2. Preflight checks
    print("\n🔍 Preflight checks:")
    valid_coords = df[['CENTROID_LATITUDE', 'CENTROID_LONGITUDE']].notna().all(axis=1).sum()
    print(f"   Rows with valid coords: {valid_coords:,}")
    
    if 'COUNTRY' in df.columns:
        unique_countries = df['COUNTRY'].dropna().unique()
        print(f"   Unique countries: {len(unique_countries)}")
        print(f"   Sample: {list(unique_countries[:10])}")
    
    # 3. Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False  # Manual commits per batch
    cur = conn.cursor()
    
    # 4. Clean old LATAM data from security_events
    print("\n🧹 Cleaning old LATAM data from security_events...")
    cur.execute("""
        DELETE FROM sofia.security_events 
        WHERE source = 'ACLED_AGGREGATED'
          AND source_id LIKE 'latam_%'
    """)
    deleted = cur.rowcount
    conn.commit()
    print(f"   Removed {deleted:,} old records")
    
    # 5. Prepare records
    print("\n🔄 Preparing records...")
    records = []
    skipped = 0
    
    for idx, row in df.iterrows():
        # Sanitize coordinates
        lat = sanitize_value(row.get('CENTROID_LATITUDE'))
        lon = sanitize_value(row.get('CENTROID_LONGITUDE'))
        
        if lat is None or lon is None:
            skipped += 1
            continue
        
        # Sanitize other fields
        country = sanitize_value(row.get('COUNTRY', ''))
        events = sanitize_value(row.get('EVENTS', 0))
        fatalities = sanitize_value(row.get('FATALITIES', 0))
        
        # Try to derive event_date from WEEK
        event_date = None
        week_val = sanitize_value(row.get('WEEK'))
        if week_val:
            try:
                event_date = pd.to_datetime(week_val).date()
            except:
                pass
        
        # Fallback to current date if no WEEK
        if event_date is None:
            event_date = datetime.now(timezone.utc).date()
        
        # Create source_id
        unique_str = f"latam_{country}_{lat}_{lon}_{idx}"
        source_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]
        
        # Minimal raw_payload (no NaN allowed)
        raw_payload = Json({
            "source": "ACLED LATAM",
            "row_index": int(idx)
        })
        
        records.append((
            'ACLED_AGGREGATED',  # source
            source_id,
            str(country) if country else 'Unknown',  # country_name
            None,  # admin1
            None,  # city
            float(lat),
            float(lon),
            event_date,  # event_date (derived from WEEK or current)
            int(events) if events else 0,
            int(fatalities) if fatalities else 0,
            raw_payload  # JSON-safe
        ))
    
    print(f"   Prepared {len(records):,} records ({skipped:,} skipped)")
    
    # 6. Insert in batches
    print(f"\n💾 Inserting in batches of {BATCH_SIZE:,}...")
    total_inserted = 0
    
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        
        try:
            execute_values(cur, """
                INSERT INTO sofia.security_events (
                    source, source_id, country_name, admin1, city,
                    latitude, longitude, event_date, event_count, fatalities, raw_payload
                ) VALUES %s
                ON CONFLICT (source, source_id) DO NOTHING
            """, batch, page_size=1000)
            
            conn.commit()
            total_inserted += len(batch)
            
            if (i // BATCH_SIZE + 1) % 10 == 0:
                print(f"   Progress: {total_inserted:,} / {len(records):,} ({total_inserted/len(records)*100:.1f}%)")
        
        except Exception as e:
            print(f"   ❌ Batch {i//BATCH_SIZE + 1} failed: {e}")
            conn.rollback()
            
            # Check for locks
            cur.execute("""
                SELECT pid, state, wait_event_type, wait_event, 
                       LEFT(query, 50) as query_snippet
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND state != 'idle'
                ORDER BY state, pid
            """)
            print("\n   Active sessions:")
            for row in cur.fetchall():
                print(f"     PID {row[0]}: {row[1]} | {row[2]} | {row[3]} | {row[4]}")
            
            raise
    
    print(f"\n   ✅ Total inserted: {total_inserted:,}")
    
    # 7. Verify
    print("\n📊 Verification:")
    cur.execute("""
        SELECT COUNT(*) FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
    """)
    total = cur.fetchone()[0]
    print(f"   Total ACLED_AGGREGATED in security_events: {total:,}")
    
    # LATAM countries
    cur.execute("""
        SELECT country_name, COUNT(*) as cnt
        FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
          AND country_name IN ('Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Mexico', 'Venezuela')
        GROUP BY country_name
        ORDER BY cnt DESC
    """)
    latam = cur.fetchall()
    if latam:
        print(f"\n   🌎 LATAM countries found: {len(latam)}")
        for country, cnt in latam:
            print(f"     {country}: {cnt:,}")
    else:
        print("\n   ⚠️  No LATAM countries found (check country names)")
    
    conn.close()
    print("\n" + "="*70)
    print("✅ IMPORT COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. python scripts/normalize-acled-to-observations-v3.py")
    print("2. python scripts/refresh_view.py")
    print("3. Verify API: curl http://localhost:8000/api/security/countries")

if __name__ == "__main__":
    main()
