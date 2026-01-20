#!/usr/bin/env python3
"""
Verify ACLED data in sofia.security_events table
Check if we have data from all continents
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', '91.98.158.19')),
    'port': os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'dbs_sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia'))
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 70)
print("ACLED DATA VERIFICATION")
print("=" * 70)

# Total records
cursor.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(latitude) as with_geo,
        COUNT(DISTINCT country_name) as countries,
        MIN(event_date) as earliest,
        MAX(event_date) as latest
    FROM sofia.security_events
    WHERE source = 'ACLED'
""")

row = cursor.fetchone()
print(f"\n✅ Security Events Summary (ACLED):")
print(f"  Total records: {row[0]:,}")
print(f"  With geo: {row[1]:,}")
print(f"  Countries: {row[2]}")
print(f"  Date range: {row[3]} to {row[4]}")

# Top 30 countries by events
cursor.execute("""
    SELECT country_name, COUNT(*) as events, SUM(fatalities) as fatalities
    FROM sofia.security_events
    WHERE source = 'ACLED' AND latitude IS NOT NULL
    GROUP BY country_name
    ORDER BY COUNT(*) DESC
    LIMIT 30
""")

print(f"\n📊 Top 30 countries by events:")
print(f"{'Country':<30} {'Events':>10} {'Fatalities':>12}")
print("-" * 55)

key_countries = {
    'Ukraine', 'United States', 'Brazil', 'Mexico', 'Syria',
    'Yemen', 'Myanmar', 'Philippines', 'India', 'Nigeria',
    'Ethiopia', 'Somalia', 'Afghanistan', 'Pakistan'
}
found_countries = set()

for row in cursor.fetchall():
    country, events, fatalities = row
    print(f"{country:<30} {events:>10,} {fatalities or 0:>12,}")
    if country in key_countries:
        found_countries.add(country)

# Check for key regions
print(f"\n🌍 Regional Coverage Check:")
print(f"  Africa: {'✅' if any(c in found_countries for c in ['Nigeria', 'Ethiopia', 'Somalia']) else '❌'}")
print(f"  Europe: {'✅' if 'Ukraine' in found_countries else '❌'} (Ukraine)")
print(f"  Americas: {'✅' if any(c in found_countries for c in ['United States', 'Brazil', 'Mexico']) else '❌'}")
print(f"  Middle East: {'✅' if any(c in found_countries for c in ['Syria', 'Yemen']) else '❌'}")
print(f"  Asia: {'✅' if any(c in found_countries for c in ['Myanmar', 'Philippines', 'India']) else '❌'}")

print(f"\n🔍 Key Countries Found: {len(found_countries)}/{len(key_countries)}")
for country in sorted(found_countries):
    print(f"  ✅ {country}")

missing = key_countries - found_countries
if missing:
    print(f"\n⚠️  Missing Expected Countries:")
    for country in sorted(missing):
        print(f"  ❌ {country}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("Next: Reload map at http://172.27.140.239:3001/map")
print("=" * 70)
