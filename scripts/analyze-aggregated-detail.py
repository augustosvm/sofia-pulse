#!/usr/bin/env python3
"""
Detailed analysis of aggregated ACLED data
To understand what we actually have
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

cur = conn.cursor()

print("="*70)
print("DETAILED ACLED AGGREGATED DATA ANALYSIS")
print("="*70)

# Ukraine detailed
print("\nUKRAINE DETAILED:")
cur.execute("""
    SELECT 
        EXTRACT(YEAR FROM event_date) as year,
        COUNT(*) as records,
        SUM(event_count) as total_events,
        SUM(fatalities) as total_deaths
    FROM sofia.security_events
    WHERE source = 'ACLED_AGGREGATED'
      AND country_name ILIKE '%ukraine%'
    GROUP BY year
    ORDER BY year DESC
""")
for row in cur.fetchall():
    print(f"  {int(row[0])}: {row[1]:,} records, {row[2]:,} events, {row[3]:,} deaths")

# Iran
print("\nIRAN:")
cur.execute("""
    SELECT 
        COUNT(*) as records,
        SUM(event_count) as total_events,
        SUM(fatalities) as total_deaths
    FROM sofia.security_events
    WHERE source = 'ACLED_AGGREGATED'
      AND country_name ILIKE '%iran%'
""")
row = cur.fetchone()
if row and row[0]:
    print(f"  {row[0]:,} records, {row[1]:,} events, {row[2]:,} deaths")
else:
    print("  NOT FOUND in aggregated data")

# Check raw acled_aggregated.regional
print("\nRAW REGIONAL DATA:")
cur.execute("""
    SELECT country, region, SUM(events) as total_events, SUM(fatalities) as deaths
    FROM acled_aggregated.regional
    WHERE country ILIKE '%ukraine%'
    GROUP BY country, region
""")
for row in cur.fetchall():
    print(f"  Ukraine ({row[1]}): {row[2]:,} events, {row[3]:,} deaths")

cur.execute("""
    SELECT country, region, SUM(events) as total_events, SUM(fatalities) as deaths
    FROM acled_aggregated.regional
    WHERE country ILIKE '%iran%'
    GROUP BY country, region
""")
results = cur.fetchall()
if results:
    for row in results:
        print(f"  Iran ({row[1]}): {row[2]:,} events, {row[3]:,} deaths")
else:
    print("  Iran: NOT FOUND in regional data")

# Top countries by fatalities
print("\nTOP 10 COUNTRIES BY FATALITIES (aggregated):")
cur.execute("""
    SELECT country, SUM(events) as total_events, SUM(fatalities) as deaths
    FROM acled_aggregated.regional
    GROUP BY country
    ORDER BY deaths DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,} events, {row[2]:,} deaths")

# Date range
print("\nDATE RANGE:")
cur.execute("""
    SELECT MIN(year) as min_year, MAX(year) as max_year
    FROM acled_aggregated.regional
""")
min_year, max_year = cur.fetchone()
print(f"  Years: {min_year} to {max_year}")

cur.close()
conn.close()

print("\n" + "="*70)
print("CONCLUSION:")
print("- Aggregated data is SUMMARY data (monthly/yearly totals)")
print("- NOT individual events with details")
print("- Good for trends, BAD for real-time monitoring")
print("="*70)
