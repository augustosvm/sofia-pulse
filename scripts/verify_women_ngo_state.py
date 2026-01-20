#!/usr/bin/env python3
"""Step 0: Verify database reality for Women/NGO enterprise hardening."""
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

print("=" * 70)
print("STEP 0.2: Base tables existence and columns")
print("=" * 70)

# Check required tables
required = ['acled_aggregated', 'countries', 'industry_signals', 'signal_country_map']
for table in required:
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema='sofia' AND table_name=%s
    """, (table,))
    exists = cur.fetchone()[0] > 0
    print(f"\n{'✅' if exists else '❌'} sofia.{table}: {'EXISTS' if exists else 'NOT FOUND'}")
    
    if exists:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema='sofia' AND table_name=%s
            ORDER BY ordinal_position
        """, (table,))
        cols = cur.fetchall()
        print(f"   Columns: {[c[0] for c in cols[:10]]}{'...' if len(cols) > 10 else ''}")

print("\n" + "=" * 70)
print("STEP 0.3: MVs existence check")
print("=" * 70)

mvs_to_check = ['mv_women_intelligence_by_country', 'mv_ngo_coverage_by_country']
for mv in mvs_to_check:
    cur.execute("""
        SELECT COUNT(*) FROM pg_matviews 
        WHERE schemaname='sofia' AND matviewname=%s
    """, (mv,))
    exists = cur.fetchone()[0] > 0
    print(f"{'✅' if exists else '❌'} sofia.{mv}: {'EXISTS' if exists else 'NOT FOUND'}")
    
    if exists:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{mv}")
        count = cur.fetchone()[0]
        print(f"   Rows: {count}")
        
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema='sofia' AND table_name=%s
        """, (mv,))
        cols = [r[0] for r in cur.fetchall()]
        print(f"   Columns: {cols}")

print("\n" + "=" * 70)
print("STEP 0.4: ngo_keyword_rules table check")
print("=" * 70)

cur.execute("""
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema='sofia' AND table_name='ngo_keyword_rules'
""")
exists = cur.fetchone()[0] > 0
print(f"{'✅' if exists else '❌'} sofia.ngo_keyword_rules: {'EXISTS' if exists else 'NOT FOUND'}")

if exists:
    cur.execute("SELECT COUNT(*) FROM sofia.ngo_keyword_rules")
    count = cur.fetchone()[0]
    print(f"   Rows: {count}")
    cur.execute("SELECT * FROM sofia.ngo_keyword_rules LIMIT 5")
    print(f"   Sample: {cur.fetchall()}")

print("\n" + "=" * 70)
print("STEP 0.5: Check for gender-specific fields in acled_aggregated")
print("=" * 70)

cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='acled_aggregated'
    AND (column_name ILIKE '%gender%' OR column_name ILIKE '%women%' 
         OR column_name ILIKE '%female%' OR column_name ILIKE '%gbv%')
""")
gender_cols = cur.fetchall()
if gender_cols:
    print(f"✅ Gender-specific columns found: {[c[0] for c in gender_cols]}")
else:
    print("❌ NO gender-specific columns found in acled_aggregated")
    print("   -> women_specific_events MUST be NULL (no data source)")

cur.close()
conn.close()
print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
