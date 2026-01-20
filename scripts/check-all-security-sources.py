#!/usr/bin/env python3
"""
Check all security data sources and normalize to security_events
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
print("ALL SECURITY DATA SOURCES")
print("="*70)

# Check sofia.gdelt_events
print("\n1. GDELT EVENTS:")
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' AND table_name = 'gdelt_events'
    )
""")
if cur.fetchone()[0]:
    cur.execute("SELECT COUNT(*), MIN(event_date), MAX(event_date) FROM sofia.gdelt_events")
    count, min_date, max_date = cur.fetchone()
    print(f"   EXISTS: {count:,} events ({min_date} to {max_date})")
    
    # Ukraine
    cur.execute("""
        SELECT COUNT(*) FROM sofia.gdelt_events
        WHERE country_name ILIKE '%ukraine%' OR location ILIKE '%ukraine%'
    """)
    ukraine = cur.fetchone()[0]
    if ukraine:
        print(f"   Ukraine: {ukraine:,} events")
else:
    print("   DOES NOT EXIST")

# Check sofia.security_events
print("\n2. SECURITY EVENTS (current):")
cur.execute("""
    SELECT source, COUNT(*), SUM(COALESCE(fatalities, 0))
    FROM sofia.security_events
    GROUP BY source
    ORDER BY COUNT(*) DESC
""")
for source, count, deaths in cur.fetchall():
    print(f"   {source}: {count:,} events, {deaths:,} deaths")

# Check acled_aggregated.regional
print("\n3. ACLED AGGREGATED:")
cur.execute("""
    SELECT COUNT(*), SUM(events), SUM(fatalities)
    FROM acled_aggregated.regional
""")
count, events, deaths = cur.fetchone()
print(f"   {count:,} records, {events:,} events, {deaths:,} deaths")

# Check sofia.acled_events
print("\n4. ACLED EVENTS (if exists):")
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' AND table_name = 'acled_events'
    )
""")
if cur.fetchone()[0]:
    cur.execute("SELECT COUNT(*), SUM(fatalities) FROM sofia.acled_events")
    count, deaths = cur.fetchone()
    print(f"   EXISTS: {count:,} events, {deaths:,} deaths")
else:
    print("   DOES NOT EXIST")

cur.close()
conn.close()

print("\n" + "="*70)
print("NEXT STEP: Normalize GDELT to security_events")
print("="*70)
