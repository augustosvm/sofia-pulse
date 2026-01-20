#!/usr/bin/env python3
"""
ACLED Coverage Diagnostic - Simple Version
"""

import os
import sys
from pathlib import Path
import psycopg2

# Load .env
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
print("🔍 ACLED COVERAGE DIAGNOSTIC")
print("="*70)

# 1) Check sofia.acled_events
print("\n1️⃣  EVENT-LEVEL DATA (sofia.acled_events)")
print("="*70)

try:
    cursor.execute("SELECT COUNT(DISTINCT country) FROM sofia.acled_events")
    count = cursor.fetchone()[0]
    print(f"   Total countries: {count}")
    
    cursor.execute("""
        SELECT country, COUNT(*) as events, MAX(event_date) as latest
        FROM sofia.acled_events
        GROUP BY country
        ORDER BY events DESC
        LIMIT 10
    """)
    print("\n   Top 10 countries:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} events (latest: {row[2]})")
    
    cursor.execute("""
        SELECT country, COUNT(*) as events
        FROM sofia.acled_events
        WHERE country IN ('Ukraine', 'Russia', 'Israel', 'United States of America')
        GROUP BY country
    """)
    results = cursor.fetchall()
    if results:
        print("\n   Specific countries:")
        for row in results:
            print(f"   • {row[0]}: {row[1]} events")
    else:
        print("\n   ⚠️  Ukraine, Russia, Israel, USA NOT FOUND")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2) Check acled_aggregated.regional
print("\n\n2️⃣  AGGREGATED REGIONAL DATA")
print("="*70)

try:
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT country) FROM acled_aggregated.regional")
    total, countries = cursor.fetchone()
    print(f"   Total rows: {total:,}")
    print(f"   Total countries: {countries}")
    
    cursor.execute("""
        SELECT region, COUNT(*) as records, COUNT(DISTINCT country) as countries
        FROM acled_aggregated.regional
        GROUP BY region
        ORDER BY region
    """)
    print("\n   By region:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]:,} records, {row[2]} countries")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3) Check metadata
print("\n\n3️⃣  METADATA")
print("="*70)

try:
    cursor.execute("""
        SELECT dataset_slug, total_rows, collected_at
        FROM acled_metadata.datasets
        WHERE dataset_slug ILIKE '%aggregated%'
        ORDER BY collected_at DESC
    """)
    print("\n   Collected datasets:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]:,} rows (collected: {row[2]})")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4) Check materialized view
print("\n\n4️⃣  MATERIALIZED VIEW (mv_security_geo_points)")
print("="*70)

try:
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT country_name) FROM mv_security_geo_points")
    total, countries = cursor.fetchone()
    print(f"   Total points: {total:,}")
    print(f"   Total countries: {countries}")
    
    cursor.execute("""
        SELECT country_name, COUNT(*) as points
        FROM mv_security_geo_points
        GROUP BY country_name
        ORDER BY points DESC
        LIMIT 15
    """)
    print("\n   Top 15 countries:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]:,} points")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

cursor.close()
conn.close()

print("\n" + "="*70)
print("✅ Diagnostic complete!")
print("="*70)
