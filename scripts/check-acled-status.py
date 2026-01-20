#!/usr/bin/env python3
"""
Quick check of ACLED data status
"""
import os
import sys
from pathlib import Path
import psycopg2

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

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER", "sofia"),
    password=os.getenv("POSTGRES_PASSWORD", ""),
    database=os.getenv("POSTGRES_DB", "sofia_db"),
)
conn.autocommit = True
cursor = conn.cursor()

print("="*70)
print("📊 ACLED DATA STATUS")
print("="*70)

# Check acled_aggregated.regional
print("\n1. ACLED AGGREGATED REGIONAL:")
try:
    cursor.execute("SELECT COUNT(*) FROM acled_aggregated.regional")
    total = cursor.fetchone()[0]
    print(f"   Total records: {total:,}")
    
    if total > 0:
        cursor.execute("""
            SELECT region, COUNT(*) as records
            FROM acled_aggregated.regional
            GROUP BY region
            ORDER BY region
        """)
        print("\n   By region:")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]:,} records")
    else:
        print("   ⚠️  Table is EMPTY")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check acled_metadata.datasets
print("\n2. ACLED METADATA:")
try:
    cursor.execute("""
        SELECT dataset_slug, total_rows, collected_at
        FROM acled_metadata.datasets
        WHERE dataset_slug ILIKE '%aggregated%'
        ORDER BY collected_at DESC
    """)
    results = cursor.fetchall()
    if results:
        print("\n   Downloaded datasets:")
        for row in results:
            print(f"   • {row[0]}: {row[1]:,} rows (collected: {row[2]})")
    else:
        print("   ⚠️  No aggregated datasets in metadata")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check sofia.acled_events (event-level)
print("\n3. ACLED EVENTS (event-level):")
try:
    cursor.execute("SELECT COUNT(*) FROM sofia.acled_events")
    total = cursor.fetchone()[0]
    print(f"   Total events: {total:,}")
    
    if total > 0:
        cursor.execute("""
            SELECT country, COUNT(*) as events
            FROM sofia.acled_events
            GROUP BY country
            ORDER BY events DESC
            LIMIT 5
        """)
        print("\n   Top 5 countries:")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]:,} events")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check for downloaded files
print("\n4. DOWNLOADED FILES:")
data_dir = Path(__file__).parent.parent / "data" / "acled" / "raw"
if data_dir.exists():
    regional_dirs = [d for d in data_dir.iterdir() if d.is_dir() and "aggregated" in d.name]
    if regional_dirs:
        print(f"\n   Found {len(regional_dirs)} regional dataset folders:")
        for d in sorted(regional_dirs):
            xlsx_files = list(d.glob("**/*.xlsx"))
            if xlsx_files:
                for f in xlsx_files:
                    size_mb = f.stat().st_size / (1024 * 1024)
                    print(f"   • {d.name}: {f.name} ({size_mb:.1f} MB)")
    else:
        print("   ⚠️  No regional dataset folders found")
else:
    print(f"   ⚠️  Data directory not found: {data_dir}")

cursor.close()
conn.close()

print("\n" + "="*70)
