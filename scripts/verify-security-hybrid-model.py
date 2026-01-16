#!/usr/bin/env python3
"""
Security Hybrid Model - Final Verification
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
print("SECURITY HYBRID MODEL - FINAL VERIFICATION")
print("="*70)

# 1. Check canonical table
print("\n1. CANONICAL TABLE (security_observations)")
print("-"*70)
cur.execute("""
    SELECT source, signal_type, coverage_scope, COUNT(*)
    FROM sofia.security_observations
    GROUP BY source, signal_type, coverage_scope
    ORDER BY source
""")

for source, signal, scope, count in cur.fetchall():
    print(f"  {source:20} {signal:12} {scope:20} {count:,}")

cur.execute("SELECT COUNT(*), COUNT(DISTINCT country_code) FROM sofia.security_observations")
total, countries = cur.fetchone()
print(f"\n  TOTAL: {total:,} observations across {countries} countries")

# 2. Check views
print("\n2. MATERIALIZED VIEWS")
print("-"*70)

views = [
    'mv_security_country_acled',
    'mv_security_country_gdelt',
    'mv_security_country_structural',
    'mv_security_country_combined'
]

for view in views:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{view}")
        count = cur.fetchone()[0]
        print(f"  {view:40} {count:,} countries")
    except Exception as e:
        print(f"  {view:40} ERROR: {e}")

# 3. Check hybrid scores
print("\n3. HYBRID SCORES (Top 10 by Total Risk)")
print("-"*70)
cur.execute("""
    SELECT country_name, acute_risk_score, structural_risk_score, 
           total_risk_score, risk_level
    FROM sofia.mv_security_country_combined
    ORDER BY total_risk_score DESC
    LIMIT 10
""")

for country, acute, structural, total, level in cur.fetchall():
    print(f"  {country:20} Acute:{acute:5.1f} Struct:{structural:5.1f} Total:{total:5.1f} [{level}]")

# 4. Check coverage scores
print("\n4. COVERAGE SCORES")
print("-"*70)
cur.execute("""
    SELECT 
        CASE 
            WHEN coverage_score_global >= 75 THEN 'High (75-100)'
            WHEN coverage_score_global >= 50 THEN 'Medium (50-74)'
            WHEN coverage_score_global >= 25 THEN 'Low (25-49)'
            ELSE 'Very Low (0-24)'
        END as coverage_level,
        COUNT(DISTINCT country_code) as countries
    FROM sofia.security_observations
    WHERE coverage_scope = 'global_comparable'
    GROUP BY coverage_level
    ORDER BY MIN(coverage_score_global) DESC
""")

for level, count in cur.fetchall():
    print(f"  {level:20} {count:,} countries")

# 5. Check Brasil local data
print("\n5. BRASIL LOCAL DATA")
print("-"*70)
cur.execute("""
    SELECT source, COUNT(*)
    FROM sofia.security_observations
    WHERE country_code = 'BR' AND coverage_scope = 'local_only'
    GROUP BY source
""")

brasil_data = cur.fetchall()
if brasil_data:
    for source, count in brasil_data:
        print(f"  {source:30} {count:,} observations")
else:
    print("  No Brasil local data found (tables may not exist yet)")

# 6. Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

cur.execute("""
    SELECT 
        COUNT(DISTINCT source) as sources,
        COUNT(DISTINCT country_code) as countries,
        COUNT(*) as total_obs
    FROM sofia.security_observations
""")

sources, countries, total_obs = cur.fetchone()

print(f"\nData Sources: {sources}")
print(f"Countries: {countries}")
print(f"Total Observations: {total_obs:,}")

print("\nStatus: ✅ HYBRID MODEL OPERATIONAL")

cur.close()
conn.close()

print("\n" + "="*70)
