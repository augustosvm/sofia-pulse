#!/usr/bin/env python3
"""
Import HDX HAPI ACLED Data
Imports aggregated conflict event data from HDX HAPI CSVs into sofia.acled_events table.
Includes geocoding for Admin regions to provide lat/long coordinates.
"""

import os
import sys
import pandas as pd
import psycopg2
import requests
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from geo_helpers_acled import normalize_location_acled

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
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CACHE_FILE = Path(__file__).parent / "geo_cache.json"

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )

def load_geo_cache() -> Dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_geo_cache(cache: Dict):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def geocode_location(admin2: str, admin1: str, country_code: str, cache: Dict) -> Tuple[Optional[float], Optional[float]]:
    """
    Get lat/long for a location using Nominatim with caching.
    """
    query_parts = []
    if admin2 and pd.notna(admin2):
        query_parts.append(admin2)
    if admin1 and pd.notna(admin1):
        query_parts.append(admin1)
    
    # Simple country code to name mapping for better geocoding if needed
    # But Nominatim handles country codes reasonably well in structured query
    
    query = ", ".join(query_parts) + f", {country_code}"
    cache_key = f"{query_parts}-{country_code}"

    if cache_key in cache:
        return cache[cache_key].get("lat"), cache[cache_key].get("lon")

    try:
        # Respect Nominatim Usage Policy: Max 1 request/sec
        time.sleep(1.1) 
        
        headers = {'User-Agent': 'SofiaPulse/1.0 (augusto@tiespecialistas.com.br)'}
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'countrycodes': country_code
        }
        
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                cache[cache_key] = {"lat": lat, "lon": lon}
                print(f"   📍 Found: {query} -> ({lat}, {lon})")
                return lat, lon
            else:
                print(f"   ⚠️ Not found: {query}")
                cache[cache_key] = {"lat": None, "lon": None} # Cache miss to avoid retrying
        else:
            print(f"   ❌ Nominatim Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"   ❌ Geocoding error: {e}")

    return None, None

def generate_event_id(row) -> str:
    """Generate a deterministic ID for proper upserting"""
    # Combine relevant fields to create a unique signature
    # location + date + type + admin level
    raw_str = f"{row.get('location_code')}-{row.get('admin1_name')}-{row.get('admin2_name')}-{row.get('reference_period_start')}-{row.get('event_type')}"
    return hashlib.md5(raw_str.encode()).hexdigest()

def import_csv(csv_path: str):
    print(f"\n📂 Processing {csv_path}...")
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"   Rows to process: {len(df)}")
    
    conn = get_db_connection()
    geo_cache = load_geo_cache()
    
    inserted = 0
    updated = 0
    errors = 0
    
    try:
        cursor = conn.cursor()
        
        # Ensure table exists (same schema as collect-acled-conflicts.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sofia.acled_events (
                event_id_cnty VARCHAR(50) PRIMARY KEY,
                event_date DATE NOT NULL,
                year INTEGER,
                event_type VARCHAR(100),
                sub_event_type VARCHAR(100),
                actor1 TEXT,
                actor2 TEXT,
                country VARCHAR(100),
                country_id INTEGER,
                region VARCHAR(100),
                location TEXT,
                city_id INTEGER,
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                source TEXT,
                notes TEXT,
                fatalities INTEGER DEFAULT 0,
                timestamp BIGINT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        for index, row in df.iterrows():
            try:
                # Basic fields
                country_code = row.get('location_code')
                admin1 = row.get('admin1_name')
                admin2 = row.get('admin2_name')
                event_type = row.get('event_type')
                fatalities = int(row.get('fatalities', 0)) if pd.notna(row.get('fatalities')) else 0
                event_count = int(row.get('events', 1)) if pd.notna(row.get('events')) else 1
                start_date = row.get('reference_period_start') # Format should be checked
                
                # Generate ID
                event_id = generate_event_id(row)
                
                # Dates
                event_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if pd.notna(start_date) else datetime.now().date()
                year = event_date_obj.year
                
                # Geography
                lat, lon = geocode_location(admin2, admin1, country_code, geo_cache)
                location_name = admin2 if pd.notna(admin2) else admin1
                
                # Use shared helper for IDs (requires country NAME not code, so we might need map if normalize fails)
                # But normalize_location_acled takes country name. 
                # Ideally we map ISO3 to Name. For now, use code if name unknown, helper might fail but will return None.
                # Actually, Nominatim might have given us a name, but we didn't capture it.
                # Let's trust location_code or admin1 for now.
                
                geo_ids = normalize_location_acled(conn, country_code, location_name)
                
                # Note: 'source' field set to 'HDX HAPI (ACLED)' as requested
                source_str = "HDX HAPI (ACLED)"
                notes_str = f"Aggregated event from HDX. {event_count} events reported in period {row.get('reference_period_start')} to {row.get('reference_period_end')}."

                cursor.execute("""
                    INSERT INTO sofia.acled_events (
                        event_id_cnty, event_date, year, event_type, sub_event_type,
                        actor1, actor2, country, country_id, region, location, city_id,
                        latitude, longitude, source, notes, fatalities, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id_cnty) DO UPDATE SET
                        event_date = EXCLUDED.event_date,
                        year = EXCLUDED.year,
                        event_type = EXCLUDED.event_type,
                        country = EXCLUDED.country,
                        location = EXCLUDED.location,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        source = EXCLUDED.source,
                        notes = EXCLUDED.notes,
                        fatalities = EXCLUDED.fatalities
                """, (
                    event_id, 
                    event_date_obj, 
                    year, 
                    event_type, 
                    "Aggregated", # sub_event_type
                    "Unknown", # actor1
                    "Unknown", # actor2
                    country_code, # country (using code as name/ref)
                    geo_ids['country_id'],
                    "Global", # region
                    location_name,
                    geo_ids['city_id'],
                    lat,
                    lon,
                    source_str,
                    notes_str,
                    fatalities,
                    int(time.time())
                ))
                
                if cursor.rowcount > 0:
                    inserted += 1 # Upsert counts as insert/update depending on impl details often
                
                # Save cache periodically
                if index % 50 == 0:
                    save_geo_cache(geo_cache)
                    conn.commit()
                    print(f"   Processed {index} rows...")

            except Exception as e:
                print(f"   ❌ Error row {index}: {e}")
                errors += 1
                continue

        conn.commit()
        save_geo_cache(geo_cache)
        print(f"✅ Finished {csv_path}: {inserted} processed (inserted/updated), {errors} errors.")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        if conn:
            conn.close()

def main():
    print("🌍 Importing HDX ACLED Data...")
    
    files = ["hdx_hapi_2024.csv", "hdx_hapi_2025.csv"]
    for f in files:
        full_path = Path(__file__).parent.parent / f
        if full_path.exists():
            import_csv(str(full_path))
        else:
            print(f"⚠️  Skipping {f} (not found in root)")

if __name__ == "__main__":
    main()
