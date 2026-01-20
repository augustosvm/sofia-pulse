#!/usr/bin/env python3
"""
Check GDELT data availability
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
print("GDELT DATA CHECK")
print("="*70)

# Find GDELT tables
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_name ILIKE '%gdelt%'
    ORDER BY table_schema, table_name
""")

gdelt_tables = cur.fetchall()

if gdelt_tables:
    print(f"\nFound {len(gdelt_tables)} GDELT table(s):")
    for schema, table in gdelt_tables:
        print(f"\n  {schema}.{table}")
        
        # Get count and sample
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cur.fetchone()[0]
        print(f"    Records: {count:,}")
        
        # Get columns
        cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position
            LIMIT 20
        """)
        cols = [row[0] for row in cur.fetchall()]
        print(f"    Columns: {', '.join(cols[:10])}...")
        
        # Check for Ukraine
        if 'country' in [c.lower() for c in cols] or 'actor1countrycode' in [c.lower() for c in cols]:
            try:
                cur.execute(f"""
                    SELECT COUNT(*) FROM {schema}.{table}
                    WHERE country ILIKE '%ukraine%' 
                       OR actor1countrycode = 'UKR'
                       OR actor2countrycode = 'UKR'
                """)
                ukraine_count = cur.fetchone()[0]
                if ukraine_count:
                    print(f"    Ukraine: {ukraine_count:,} records")
            except:
                pass
else:
    print("\nNo GDELT tables found")
    print("Searching for any tables with conflict/event data...")
    
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name ILIKE '%conflict%'
           OR table_name ILIKE '%event%'
           OR table_name ILIKE '%security%'
        ORDER BY table_schema, table_name
    """)
    
    for schema, table in cur.fetchall():
        print(f"  {schema}.{table}")

cur.close()
conn.close()

print("\n" + "="*70)
