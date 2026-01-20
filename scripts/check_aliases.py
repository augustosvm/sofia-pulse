#!/usr/bin/env python3
"""Check country_aliases table schema."""
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

print("Columns in country_aliases:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='country_aliases'
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\nSample data:")
cur.execute("SELECT * FROM sofia.country_aliases LIMIT 5")
for row in cur.fetchall():
    print(f"  {row}")

print("\nTotal aliases:", end=" ")
cur.execute("SELECT COUNT(*) FROM sofia.country_aliases")
print(cur.fetchone()[0])

cur.close()
conn.close()
