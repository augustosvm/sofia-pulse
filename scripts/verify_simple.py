#!/usr/bin/env python3
"""Step 0: Verify database reality - simple output."""
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

print("STEP 0: DATABASE EVIDENCE")
print("=" * 60)

# MVs
for mv in ['mv_women_intelligence_by_country', 'mv_ngo_coverage_by_country']:
    cur.execute("SELECT COUNT(*) FROM pg_matviews WHERE schemaname='sofia' AND matviewname=%s", (mv,))
    exists = cur.fetchone()[0] > 0
    if exists:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{mv}")
        count = cur.fetchone()[0]
        print(f"MV {mv}: EXISTS ({count} rows)")
    else:
        print(f"MV {mv}: NOT FOUND")

# ngo_keyword_rules
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia' AND table_name='ngo_keyword_rules'")
if cur.fetchone()[0] > 0:
    cur.execute("SELECT COUNT(*) FROM sofia.ngo_keyword_rules")
    print(f"TABLE ngo_keyword_rules: EXISTS ({cur.fetchone()[0]} rows)")
else:
    print("TABLE ngo_keyword_rules: NOT FOUND")

# Gender columns in acled
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='acled_aggregated'
    AND (column_name ILIKE '%gender%' OR column_name ILIKE '%women%')
""")
gender = cur.fetchall()
print(f"Gender columns in acled_aggregated: {[c[0] for c in gender] if gender else 'NONE'}")

# MV columns check
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='mv_women_intelligence_by_country'
""")
cols = [r[0] for r in cur.fetchall()]
print(f"Women MV columns: {cols}")

cur.close()
conn.close()
