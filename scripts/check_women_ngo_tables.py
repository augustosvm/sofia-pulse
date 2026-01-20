#!/usr/bin/env python3
"""Check women and NGO tables in database."""
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

print("=" * 60)
print("TABLES WITH 'women' or 'gender' or 'organization' or 'ngo':")
print("=" * 60)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='sofia' 
    AND (
        table_name LIKE '%women%' 
        OR table_name LIKE '%gender%'
        OR table_name LIKE '%organization%'
        OR table_name LIKE '%ngo%'
        OR table_name LIKE '%violence%'
        OR table_name LIKE '%gbv%'
    )
""")
tables = [r[0] for r in cur.fetchall()]
print(f"Found {len(tables)} tables:")
for t in tables:
    print(f"  - {t}")

# Check columns for each table
for table in tables:
    print(f"\n{table} columns:")
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema='sofia' AND table_name='{table}'
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
    count = cur.fetchone()[0]
    print(f"  -> Rows: {count}")

# Check ACLED for violence/women related data
print("\n" + "=" * 60)
print("ACLED TABLES (potential violence/GBV source):")
print("=" * 60)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='sofia' AND table_name LIKE '%acled%'
""")
for r in cur.fetchall():
    print(f"  - {r[0]}")

# Check if acled_aggregated has useful columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='acled_aggregated'
""")
cols = [r[0] for r in cur.fetchall()]
if cols:
    print(f"\nacled_aggregated columns: {cols}")
    cur.execute("SELECT COUNT(*) FROM sofia.acled_aggregated")
    print(f"Rows: {cur.fetchone()[0]}")
    # Check for country_code
    if 'country_code' in cols:
        cur.execute("SELECT DISTINCT country_code FROM sofia.acled_aggregated LIMIT 10")
        print(f"Sample countries: {[r[0] for r in cur.fetchall()]}")

# Check gdelt
print("\n" + "=" * 60)
print("GDELT (potential women/NGO source):")
print("=" * 60)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='sofia' AND table_name LIKE '%gdelt%'
""")
for r in cur.fetchall():
    print(f"  - {r[0]}")

cur.close()
conn.close()
