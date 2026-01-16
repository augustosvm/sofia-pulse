#!/usr/bin/env python3
"""
Execute migration 053 - Security Observations Canonical Table
"""
import psycopg2
import os
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
conn.autocommit = True
cur = conn.cursor()

print("="*70)
print("EXECUTING MIGRATION 053: Security Observations Canonical Table")
print("="*70)

# Read migration file
migration_file = Path(__file__).parent.parent / "migrations" / "053_security_observations_canonical.sql"
with open(migration_file, 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    cur.execute(sql)
    print("\nOK - Migration executed successfully")
    
    # Verify table creation
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = 'security_observations'
        ORDER BY ordinal_position
    """)
    
    print("\nTable structure:")
    for col, dtype in cur.fetchall():
        print(f"  {col}: {dtype}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    raise

cur.close()
conn.close()

print("\n" + "="*70)
print("MIGRATION COMPLETE")
print("="*70)
