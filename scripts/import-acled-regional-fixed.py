#!/usr/bin/env python3
"""
ACLED Regional Data Importer - Fixed Version
- Checks existing data to avoid duplicates
- Uses COPY for fast bulk insert
- Imports only missing regions
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
import pandas as pd
from datetime import datetime
from io import StringIO

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

# Regional datasets mapping
REGIONAL_DATASETS = {
    "aggregated-africa": {
        "folder": "aggregated-africa",
        "region": "Africa",
        "pattern": "*Africa*.xlsx"
    },
    "aggregated-europe-central-asia": {
        "folder": "aggregated-europe-central-asia",
        "region": "Europe and Central Asia",
        "pattern": "*Europe*.xlsx"
    },
    "aggregated-us-canada": {
        "folder": "aggregated-us-canada",
        "region": "United States and Canada",
        "pattern": "*US-and-Canada*.xlsx"
    },
    "aggregated-latin-america-caribbean": {
        "folder": "aggregated-latin-america-caribbean",
        "region": "Latin America and Caribbean",
        "pattern": "*Latin-America*.xlsx"
    },
    "aggregated-middle-east": {
        "folder": "aggregated-middle-east",
        "region": "Middle East",
        "pattern": "*Middle-East*.xlsx"
    },
    "aggregated-asia-pacific": {
        "folder": "aggregated-asia-pacific",
        "region": "Asia-Pacific",
        "pattern": "*Asia-Pacific*.xlsx"
    }
}

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )

def check_existing_regions(conn):
    """Check which regions are already imported"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT region, COUNT(*) as records
        FROM acled_aggregated.regional
        GROUP BY region
    """)
    existing = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    return existing

def import_regional_file(conn, slug, region, file_path):
    """Import a single regional file using COPY"""
    
    print(f"\n{'='*70}")
    print(f"📥 Importing: {region}")
    print(f"   File: {file_path.name}")
    print(f"{'='*70}")
    
    # Read Excel file
    print("   Reading Excel file...")
    df = pd.read_excel(file_path)
    print(f"   ✅ Loaded {len(df):,} rows")
    
    # Prepare data for COPY
    print("   Preparing data...")
    
    # Create CSV buffer
    buffer = StringIO()
    
    for idx, row in df.iterrows():
        if idx % 10000 == 0 and idx > 0:
            print(f"   Processing row {idx:,}/{len(df):,}...")
        
        # Extract fields
        country = str(row.get('country', '')).strip() if pd.notna(row.get('country')) else None
        admin1 = str(row.get('admin1', '')).strip() if pd.notna(row.get('admin1')) else None
        admin2 = str(row.get('admin2', '')).strip() if pd.notna(row.get('admin2')) else None
        year = int(row.get('year')) if pd.notna(row.get('year')) else None
        
        # Handle month
        month = None
        if pd.notna(row.get('month')):
            try:
                month = int(row.get('month'))
            except:
                pass
        
        # Handle week
        week = None
        if pd.notna(row.get('week')):
            try:
                week = int(row.get('week'))
            except:
                pass
        
        events = int(row.get('events', 0)) if pd.notna(row.get('events')) else 0
        fatalities = int(row.get('fatalities', 0)) if pd.notna(row.get('fatalities')) else 0
        
        # Event type and disorder type
        event_type = str(row.get('event_type', '')).strip() if pd.notna(row.get('event_type')) else None
        disorder_type = str(row.get('disorder_type', '')).strip() if pd.notna(row.get('disorder_type')) else None
        
        # Coordinates
        lat = float(row.get('centroid_latitude')) if pd.notna(row.get('centroid_latitude')) else None
        lon = float(row.get('centroid_longitude')) if pd.notna(row.get('centroid_longitude')) else None
        
        # Build metadata JSON (other fields)
        metadata_fields = {}
        for k, v in row.items():
            if k not in ['country', 'admin1', 'admin2', 'year', 'month', 'week', 'events', 
                        'fatalities', 'event_type', 'disorder_type', 'centroid_latitude', 'centroid_longitude']:
                if pd.notna(v):
                    if isinstance(v, (pd.Timestamp, datetime)):
                        metadata_fields[k] = v.isoformat()
                    elif isinstance(v, (int, float, str, bool)):
                        metadata_fields[k] = v
                    else:
                        metadata_fields[k] = str(v)
        
        import json
        metadata_json = json.dumps(metadata_fields) if metadata_fields else None
        
        # Write to buffer (tab-separated for COPY)
        # Format: slug, region, country, admin1, admin2, year, month, week, events, fatalities, 
        #         event_type, disorder_type, lat, lon, metadata
        buffer.write(f"{slug}\t{region}\t")
        buffer.write(f"{country or '\\N'}\t{admin1 or '\\N'}\t{admin2 or '\\N'}\t")
        buffer.write(f"{year or '\\N'}\t{month or '\\N'}\t{week or '\\N'}\t")
        buffer.write(f"{events}\t{fatalities}\t")
        buffer.write(f"{event_type or '\\N'}\t{disorder_type or '\\N'}\t")
        buffer.write(f"{lat or '\\N'}\t{lon or '\\N'}\t")
        buffer.write(f"{metadata_json or '\\N'}\n")
    
    # Insert using COPY
    print(f"   Inserting {len(df):,} records...")
    buffer.seek(0)
    
    cursor = conn.cursor()
    try:
        cursor.copy_from(
            buffer,
            'acled_aggregated.regional',
            columns=['dataset_slug', 'region', 'country', 'admin1', 'admin2', 'year', 'month', 'week',
                    'events', 'fatalities', 'event_type', 'disorder_type', 'centroid_latitude',
                    'centroid_longitude', 'metadata'],
            null='\\N'
        )
        conn.commit()
        print(f"   ✅ Inserted {len(df):,} records")
        cursor.close()
        return len(df)
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error: {e}")
        cursor.close()
        return 0

def main():
    print("="*70)
    print("🌍 ACLED REGIONAL DATA IMPORTER")
    print("="*70)
    
    # Connect to database
    conn = get_db_connection()
    
    # Check existing regions
    print("\n📊 Checking existing data...")
    existing = check_existing_regions(conn)
    
    if existing:
        print("\n   Already imported:")
        for region, count in existing.items():
            print(f"   • {region}: {count:,} records")
    else:
        print("   No data imported yet")
    
    # Find data files
    data_dir = Path(__file__).parent.parent / "data" / "acled" / "raw"
    
    if not data_dir.exists():
        print(f"\n❌ Data directory not found: {data_dir}")
        return
    
    # Import each region
    total_imported = 0
    
    for slug, config in REGIONAL_DATASETS.items():
        region = config['region']
        
        # Skip if already imported
        if region in existing:
            print(f"\n⏭️  Skipping {region} (already imported with {existing[region]:,} records)")
            continue
        
        # Find file
        folder_path = data_dir / config['folder']
        if not folder_path.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            continue
        
        # Find Excel file
        files = list(folder_path.glob("**/" + config['pattern']))
        if not files:
            print(f"\n⚠️  No Excel file found in {folder_path}")
            continue
        
        file_path = files[0]
        
        # Import
        imported = import_regional_file(conn, slug, region, file_path)
        total_imported += imported
    
    conn.close()
    
    print("\n" + "="*70)
    print(f"✅ Import complete!")
    print(f"   Total new records: {total_imported:,}")
    print("="*70)

if __name__ == "__main__":
    main()
