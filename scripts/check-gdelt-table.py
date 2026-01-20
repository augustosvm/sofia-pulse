#!/usr/bin/env python3
"""
Check GDELT table structure and data
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

print("GDELT TABLE CHECK")
print("="*70)

# Check if exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' AND table_name = 'gdelt_events'
    )
""")

if cur.fetchone()[0]:
    print("\nTable: sofia.gdelt_events EXISTS")
    
    # Get count
    cur.execute("SELECT COUNT(*), MIN(event_date), MAX(event_date) FROM sofia.gdelt_events")
    count, min_date, max_date = cur.fetchone()
    print(f"Records: {count:,}")
    print(f"Date range: {min_date} to {max_date}")
    
    # Get columns
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = 'gdelt_events'
        ORDER BY ordinal_position
    """)
    
    print("\nColumns:")
    for col, dtype in cur.fetchall():
        print(f"  {col}: {dtype}")
    
    # Sample data
    cur.execute("SELECT * FROM sofia.gdelt_events LIMIT 1")
    print("\nSample record exists:", cur.fetchone() is not None)
    
else:
    print("\nTable: sofia.gdelt_events DOES NOT EXIST")

cur.close()
conn.close()
