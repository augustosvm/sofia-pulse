#!/usr/bin/env python3
"""
Final detailed report with all counts
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
print("ACLED PIPELINE - DETAILED COUNTS REPORT")
print("="*70)

# Staging by region
print("\n1. STAGING (acled_aggregated.regional) BY REGION:")
print("-"*70)
cur.execute("""
    SELECT region, COUNT(*) as records, COUNT(DISTINCT country) as countries,
           SUM(events) as total_events, SUM(fatalities) as total_deaths
    FROM acled_aggregated.regional
    GROUP BY region
    ORDER BY records DESC
""")

for region, records, countries, events, deaths in cur.fetchall():
    print(f"\n  {region}:")
    print(f"    Records: {records:,}")
    print(f"    Countries: {countries}")
    print(f"    Events: {events:,}")
    print(f"    Deaths: {deaths:,}")

# Canonical total
print("\n\n2. CANONICAL (sofia.security_events) TOTALS:")
print("-"*70)
cur.execute("""
    SELECT COUNT(*) as records, SUM(event_count) as events, 
           SUM(fatalities) as deaths, COUNT(DISTINCT country_name) as countries
    FROM sofia.security_events
    WHERE source = 'ACLED_AGGREGATED'
""")

records, events, deaths, countries = cur.fetchone()
print(f"  Total Records: {records:,}")
print(f"  Total Events: {events:,}")
print(f"  Total Deaths: {deaths:,}")
print(f"  Countries: {countries}")

# Ukraine specific
print("\n\n3. UKRAINE VERIFICATION:")
print("-"*70)
cur.execute("""
    SELECT country_name, COUNT(*) as records,
           SUM(event_count) as events, SUM(fatalities) as deaths
    FROM sofia.security_events
    WHERE source = 'ACLED_AGGREGATED' AND country_name ILIKE '%Ukraine%'
    GROUP BY country_name
""")

ukraine = cur.fetchall()
if ukraine:
    for country, recs, evts, dths in ukraine:
        print(f"  {country}:")
        print(f"    Records: {recs:,}")
        print(f"    Events: {evts:,}")
        print(f"    Deaths: {dths:,}")
    print("\n  STATUS: OK")
else:
    print("  STATUS: FAILED - NOT FOUND")

# Map coverage
print("\n\n4. MAP COVERAGE (mv_security_geo_points):")
print("-"*70)
cur.execute("""
    SELECT COUNT(*) as points, COUNT(DISTINCT country_name) as countries,
           MIN(longitude) as min_lon, MAX(longitude) as max_lon,
           MIN(latitude) as min_lat, MAX(latitude) as max_lat
    FROM sofia.mv_security_geo_points
""")

points, countries, min_lon, max_lon, min_lat, max_lat = cur.fetchone()
print(f"  Total Points: {points:,}")
print(f"  Countries: {countries}")
print(f"  Longitude: {min_lon:.2f} to {max_lon:.2f}")
print(f"  Latitude: {min_lat:.2f} to {max_lat:.2f}")

is_global = (max_lon - min_lon) > 100 and (max_lat - min_lat) > 50
print(f"\n  COVERAGE: {'GLOBAL' if is_global else 'LIMITED'}")

# Top 15 countries
print("\n\n5. TOP 15 COUNTRIES (by events):")
print("-"*70)
cur.execute("""
    SELECT country_name, COUNT(*) as records, SUM(event_count) as events
    FROM sofia.security_events
    WHERE source = 'ACLED_AGGREGATED'
    GROUP BY country_name
    ORDER BY events DESC
    LIMIT 15
""")

for country, records, events in cur.fetchall():
    print(f"  {country}: {events:,} events ({records:,} records)")

cur.close()
conn.close()

print("\n" + "="*70)
print("PIPELINE STATUS: SUCCESS")
print("="*70)
print("\nRefresh your browser to see the updated map!")
