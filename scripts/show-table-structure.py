#!/usr/bin/env python3
import psycopg2, os
from pathlib import Path

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
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
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='security_events'
    ORDER BY ordinal_position
""")

print("sofia.security_events columns:")
for col, dtype, maxlen in cur.fetchall():
    if maxlen:
        print(f"  {col}: {dtype}({maxlen})")
    else:
        print(f"  {col}: {dtype}")

cur.close()
conn.close()
