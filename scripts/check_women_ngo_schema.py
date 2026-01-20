#!/usr/bin/env python3
"""Check detailed schema for women and NGO tables."""
import psycopg2
import os
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

load_env()
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    database=os.getenv("POSTGRES_DB", "sofia_db")
)
cur = conn.cursor()

# 1. ORGANIZATIONS TABLE
print("=" * 60)
print("ORGANIZATIONS TABLE")
print("=" * 60)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='organizations'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("SELECT COUNT(*) FROM sofia.organizations")
print(f"Rows: {cur.fetchone()[0]}")

# 2. GENDER_INDICATORS
print("\n" + "=" * 60)
print("GENDER_INDICATORS TABLE")
print("=" * 60)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='gender_indicators'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("SELECT COUNT(*) FROM sofia.gender_indicators")
cnt = cur.fetchone()[0]
print(f"Rows: {cnt}")

if cnt > 0:
    cur.execute("SELECT * FROM sofia.gender_indicators LIMIT 2")
    print("Sample:")
    for row in cur.fetchall():
        print(f"  {row}")

# 3. ACLED AGGREGATED - check columns
print("\n" + "=" * 60)
print("ACLED_AGGREGATED TABLE")
print("=" * 60)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='acled_aggregated'
    ORDER BY ordinal_position
""")
cols = []
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")
    cols.append(row[0])

cur.execute("SELECT COUNT(*) FROM sofia.acled_aggregated")
print(f"Rows: {cur.fetchone()[0]}")

# Find country column
if 'country_id' in cols:
    print("\nACLED uses country_id, need to check countries table for ISO2")
    cur.execute("SELECT DISTINCT country_id FROM sofia.acled_aggregated LIMIT 10")
    print(f"Sample country_ids: {[r[0] for r in cur.fetchall()]}")

if 'event_type' in cols:
    cur.execute("SELECT DISTINCT event_type FROM sofia.acled_aggregated LIMIT 10")
    print(f"Event types: {[r[0] for r in cur.fetchall()]}")

# Check if there are notes/tags for women-specific
if 'notes' in cols:
    cur.execute("SELECT COUNT(*) FROM sofia.acled_aggregated WHERE notes ILIKE '%women%' OR notes ILIKE '%female%'")
    print(f"Rows with women/female in notes: {cur.fetchone()[0]}")

# 4. COUNTRIES TABLE - check FK
print("\n" + "=" * 60)
print("COUNTRIES TABLE")
print("=" * 60)
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='countries'
""")
print(f"Columns: {[r[0] for r in cur.fetchall()]}")

cur.execute("SELECT id, iso_alpha2, common_name FROM sofia.countries LIMIT 5")
print("Sample:")
for row in cur.fetchall():
    print(f"  {row}")

cur.close()
conn.close()
