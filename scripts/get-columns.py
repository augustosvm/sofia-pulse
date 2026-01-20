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
    SELECT column_name
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='security_events'
    ORDER BY ordinal_position
""")

columns = [row[0] for row in cur.fetchall()]
print("Columns:", ", ".join(columns))

# Save to file
with open("security_events_columns.txt", "w") as f:
    f.write("\n".join(columns))

print(f"\nSaved to security_events_columns.txt ({len(columns)} columns)")

cur.close()
conn.close()
