#!/usr/bin/env python3
"""
Execute migration 054 - Security Hybrid Views
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
conn.autocommit = True
cur = conn.cursor()

print("="*70)
print("EXECUTING MIGRATION 054: Security Hybrid Views")
print("="*70)

migration_file = Path(__file__).parent.parent / "migrations" / "054_security_hybrid_views.sql"
with open(migration_file, 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    cur.execute(sql)
    print("\nOK - Migration executed successfully")
    
    # Verify views
    cur.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'sofia' AND table_name LIKE 'mv_security_country%'
        ORDER BY table_name
    """)
    
    print("\nViews created:")
    for (view_name,) in cur.fetchall():
        print(f"  {view_name}")
    
except Exception as e:
    print(f"\nERROR: {e}")
    raise

cur.close()
conn.close()

print("\n" + "="*70)
print("MIGRATION COMPLETE")
print("="*70)
