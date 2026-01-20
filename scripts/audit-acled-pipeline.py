#!/usr/bin/env python3
"""
ACLED Complete Pipeline Audit and Execution
"""
import psycopg2, os
from pathlib import Path

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip()

load_env()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
conn.autocommit = True
cur = conn.cursor()

print("="*70)
print("TASK 1: VERIFY REGIONS IN STAGING")
print("="*70)

cur.execute("""
    SELECT region, COUNT(*) as records, COUNT(DISTINCT country) as countries
    FROM acled_aggregated.regional
    GROUP BY region
    ORDER BY records DESC
""")

regions_found = {}
for region, records, countries in cur.fetchall():
    regions_found[region] = (records, countries)
    print(f"  {region}: {records:,} records, {countries} countries")

expected_regions = [
    "Africa",
    "Europe and Central Asia",
    "United States and Canada",
    "Latin America and Caribbean",
    "Middle East",
    "Asia-Pacific"
]

missing_regions = [r for r in expected_regions if r not in regions_found]

if missing_regions:
    print(f"\nMISSING REGIONS: {', '.join(missing_regions)}")
    print("Need to run import-acled-regional-fixed.py")
else:
    print("\nOK - All 6 regions present")

print("\n" + "="*70)
print("TASK 4: VERIFY UKRAINE IN CANONICAL")
print("="*70)

cur.execute("""
    SELECT country_name, COUNT(*) as records, 
           SUM(event_count) as total_events, 
           SUM(fatalities) as total_deaths
    FROM sofia.security_events
    WHERE source='ACLED_AGGREGATED' AND country_name ILIKE '%Ukraine%'
    GROUP BY country_name
""")

ukraine_results = cur.fetchall()
if ukraine_results:
    for country, records, events, deaths in ukraine_results:
        print(f"  {country}: {records:,} records, {events:,} events, {deaths:,} deaths")
else:
    print("  WARNING: Ukraine NOT FOUND in sofia.security_events")
    print("  Need to run normalize-acled-regional.py")

print("\n" + "="*70)
print("TASK 5: VERIFY GLOBAL COVERAGE IN MV")
print("="*70)

try:
    cur.execute("""
        SELECT 
            MIN(longitude) as min_lon, 
            MAX(longitude) as max_lon,
            MIN(latitude) as min_lat, 
            MAX(latitude) as max_lat,
            COUNT(*) as total_points,
            COUNT(DISTINCT country_name) as countries
        FROM sofia.mv_security_geo_points
    """)
    
    min_lon, max_lon, min_lat, max_lat, points, countries = cur.fetchone()
    
    print(f"  Total points: {points:,}")
    print(f"  Countries: {countries}")
    print(f"  Longitude range: {min_lon:.2f} to {max_lon:.2f}")
    print(f"  Latitude range: {min_lat:.2f} to {max_lat:.2f}")
    
    # Check if global (should span multiple continents)
    is_global = (max_lon - min_lon) > 100 and (max_lat - min_lat) > 50
    
    if is_global:
        print("\n  OK - Global coverage detected")
    else:
        print("\n  WARNING - Coverage seems limited (possibly only Africa)")
        
except Exception as e:
    print(f"  ERROR: {e}")

cur.close()
conn.close()

print("\n" + "="*70)
print("AUDIT COMPLETE")
print("="*70)
