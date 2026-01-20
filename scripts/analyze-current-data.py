#!/usr/bin/env python3
"""
Check what we actually have in the database
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
print("CURRENT DATA ANALYSIS")
print("="*70)

# Check Ukraine
print("\nUKRAINE:")
cur.execute("""
    SELECT source, COUNT(*) as events, SUM(fatalities) as deaths
    FROM sofia.security_events
    WHERE country_name ILIKE '%ukraine%'
    GROUP BY source
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,} events, {row[2]:,} deaths")

# Check Iran
print("\nIRAN:")
cur.execute("""
    SELECT source, COUNT(*) as events, SUM(fatalities) as deaths
    FROM sofia.security_events
    WHERE country_name ILIKE '%iran%'
    GROUP BY source
""")
results = cur.fetchall()
if results:
    for row in results:
        print(f"  {row[0]}: {row[1]:,} events, {row[2]:,} deaths")
else:
    print("  NOT FOUND")

# Check what sources we have
print("\nALL SOURCES:")
cur.execute("""
    SELECT source, COUNT(*) as events, SUM(fatalities) as deaths,
           MIN(event_date) as earliest, MAX(event_date) as latest
    FROM sofia.security_events
    GROUP BY source
    ORDER BY events DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,} events, {row[2]:,} deaths ({row[3]} to {row[4]})")

# Check if we have ACLED event-level data
print("\nACLED EVENT-LEVEL TABLE:")
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' 
        AND table_name = 'acled_events'
    )
""")
if cur.fetchone()[0]:
    cur.execute("SELECT COUNT(*), SUM(fatalities), MIN(event_date), MAX(event_date) FROM sofia.acled_events")
    count, deaths, earliest, latest = cur.fetchone()
    print(f"  EXISTS: {count:,} events, {deaths:,} deaths ({earliest} to {latest})")
    
    # Ukraine in event-level
    cur.execute("""
        SELECT COUNT(*), SUM(fatalities)
        FROM sofia.acled_events
        WHERE country ILIKE '%ukraine%'
    """)
    uk_events, uk_deaths = cur.fetchone()
    if uk_events:
        print(f"  Ukraine: {uk_events:,} events, {uk_deaths:,} deaths")
else:
    print("  DOES NOT EXIST")

cur.close()
conn.close()

print("\n" + "="*70)
print("CONCLUSION: Need to collect REAL event-level data from ACLED API")
print("="*70)
