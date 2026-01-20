#!/usr/bin/env python3
"""
ACLED HDX Collector (Definitive v3)
Source: HDX HAPI (ACLED Conflict Events)
Destination: sofia.security_events
Features:
- Streaming download
- Chunked processing (50k rows)
- Deterministic ID generation (SHA256)
- Native Lat/Lon from dataset (No Geocoding)
- NaN Sanitization
"""

import os
import sys
import pandas as pd
import psycopg2
import psycopg2.extras
import requests
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

# Load .env manually
def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip()

load_env()

# Configuration
HDX_PACKAGE_ID = "hdx-hapi-conflict-event"
SOURCE_NAME = "HDX_HAPI_ACLED"
CHUNK_SIZE = 50000

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )

def generate_event_id(row) -> str:
    """Generate deterministic SHA256 ID"""
    # Hash signature parts:
    # source|date|admin1|admin2|lat|lon|type|fatalities
    
    # Handle NaN/None in fields
    date = str(row.get('reference_period_start', ''))
    cntry = str(row.get('location_code', ''))
    adm1 = str(row.get('admin1_name', '')) if pd.notna(row.get('admin1_name')) else ''
    adm2 = str(row.get('admin2_name', '')) if pd.notna(row.get('admin2_name')) else ''
    # Use formatted float to avoid small precision diffs hash changes, though strict equality is safer for dedupe
    lat = f"{float(row.get('latitude', 0)):.6f}" if pd.notna(row.get('latitude')) else '0.000000'
    lon = f"{float(row.get('longitude', 0)):.6f}" if pd.notna(row.get('longitude')) else '0.000000'
    etype = str(row.get('event_type', ''))
    fat = str(int(row.get('fatalities', 0)) if pd.notna(row.get('fatalities')) else 0)
    
    raw_sig = f"{SOURCE_NAME}|{date}|{cntry}|{adm1}|{adm2}|{lat}|{lon}|{etype}|{fat}"
    return hashlib.sha256(raw_sig.encode()).hexdigest()

def sanitize_record(record):
    """Convert NaN/Inf to None for JSON/DB compliance"""
    clean = {}
    for k, v in record.items():
        if pd.isna(v):
            clean[k] = None
        elif isinstance(v, float) and (v == float('inf') or v == float('-inf')):
            clean[k] = None
        else:
            clean[k] = v
    return clean

def ensure_table_exists(conn):
    """Ensure sofia.security_events exists (minimal check)"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sofia.security_events (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                event_id TEXT NOT NULL,
                event_date TIMESTAMP WITH TIME ZONE,
                country_code TEXT,
                country_name TEXT,
                admin1 TEXT,
                admin2 TEXT,
                location_name TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                event_type TEXT,
                sub_event_type TEXT,
                fatalities INTEGER DEFAULT 0,
                events INTEGER DEFAULT 1,
                raw_payload JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT uq_security_events_source_id UNIQUE (source, event_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_security_events_source_date ON sofia.security_events(source, event_date DESC);
            CREATE INDEX IF NOT EXISTS idx_security_events_country ON sofia.security_events(country_code);
            CREATE INDEX IF NOT EXISTS idx_security_events_latlon ON sofia.security_events(latitude, longitude);
        """)
    conn.commit()

def fetch_hdx_resources():
    """Get CSV download URLs for current and previous year"""
    try:
        url = f"https://data.humdata.org/api/3/action/package_show?id={HDX_PACKAGE_ID}"
        print(f"📡 Fetching metadata from {url}...")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        resources = []
        current_year = datetime.now().year
        target_years = [str(current_year), str(current_year - 1)]
        
        for res in data['result']['resources']:
            # Filter for global Conflict Events CSVs
            # Name usually contains "global" and year
            name_lower = res['name'].lower()
            if 'global' in name_lower and 'csv' in res['format'].lower():
                for y in target_years:
                    if y in name_lower:
                        resources.append({
                            'url': res['url'],
                            'year': y,
                            'name': res['name']
                        })
        return resources
    except Exception as e:
        print(f"❌ Error fetching HDX metadata: {e}")
        return []

def process_csv_stream(url, conn):
    """Stream and process CSV in chunks"""
    print(f"⬇️  Streaming from {url}...")
    
    total_processed = 0
    total_inserted = 0
    
    try:
        # Stream request
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            # Use chunks
            for chunk in pd.read_csv(r.raw, chunksize=CHUNK_SIZE):
                
                rows_to_insert = []
                
                for _, row in chunk.iterrows():
                    # Generate ID
                    evt_id = generate_event_id(row)
                    
                    # Sanitize for raw_payload
                    cleaned_row = sanitize_record(row.to_dict())
                    
                    # Map fields
                    # HAPI fields: reference_period_start, location_code, admin1_name, admin2_name, latitude, longitude
                    # event_type, fatalities, events
                    
                    event_date = row.get('reference_period_start')
                    
                    # Ensure lat/lon are floats or None
                    lat = row.get('latitude')
                    lon = row.get('longitude')
                    if pd.isna(lat) or pd.isna(lon):
                        lat, lon = None, None
                    else:
                        lat, lon = float(lat), float(lon)

                    rows_to_insert.append((
                        SOURCE_NAME,
                        evt_id,
                        event_date,
                        str(row.get('location_code', ''))[:10], # ISO3 usually
                        str(row.get('provider_admin1_name') or row.get('admin1_name', 'Unknown')), # Fallback to admin1
                        str(row.get('admin1_name', '')),
                        str(row.get('admin2_name', '')),
                        str(row.get('admin2_name') or row.get('admin1_name', '')), # location_name fallback
                        lat,
                        lon,
                        str(row.get('event_type', '')),
                        None, # sub_event_type not always clear in HAPI aggregate, leave null
                        int(row.get('fatalities', 0)) if pd.notna(row.get('fatalities')) else 0,
                        int(row.get('events', 1)) if pd.notna(row.get('events')) else 1,
                        json.dumps(cleaned_row)
                    ))
                
                # Bulk Upsert
                if rows_to_insert:
                    with conn.cursor() as cur:
                        psycopg2.extras.execute_values(
                            cur,
                            """
                            INSERT INTO sofia.security_events (
                                source, event_id, event_date, 
                                country_code, country_name, admin1, admin2, location_name,
                                latitude, longitude, event_type, sub_event_type,
                                fatalities, events, raw_payload
                            ) VALUES %s
                            ON CONFLICT (source, event_id) DO UPDATE SET
                                event_date = EXCLUDED.event_date,
                                country_code = EXCLUDED.country_code,
                                country_name = EXCLUDED.country_name,
                                admin1 = EXCLUDED.admin1,
                                admin2 = EXCLUDED.admin2,
                                location_name = EXCLUDED.location_name,
                                latitude = EXCLUDED.latitude,
                                longitude = EXCLUDED.longitude,
                                event_type = EXCLUDED.event_type,
                                fatalities = EXCLUDED.fatalities,
                                events = EXCLUDED.events,
                                raw_payload = EXCLUDED.raw_payload,
                                updated_at = NOW()
                            """,
                            rows_to_insert
                        )
                    conn.commit()
                    total_inserted += len(rows_to_insert)
                    
                total_processed += len(chunk)
                print(f"   Processed {total_processed} rows...", end='\r')
                
        print(f"\n✅ Finished chunk: {total_processed} rows processed.")
        return total_processed

    except Exception as e:
        print(f"\n❌ Error processing stream: {e}")
        return 0

def main():
    print(f"🌍 Starting ACLED HDX Collector [{datetime.now()}]")
    
    conn = get_db_connection()
    if not conn:
        print("❌ DB Connection failed")
        return
        
    try:
        ensure_table_exists(conn)
        
        resources = fetch_hdx_resources()
        if not resources:
            print("⚠️ No suitable resources found on HDX.")
            return
            
        print(f"Found {len(resources)} resources to process.")
        
        for res in resources:
            print(f"\nProcessing {res['name']} ({res['year']})...")
            process_csv_stream(res['url'], conn)
            
        print("\n✅ Collection Complete.")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
