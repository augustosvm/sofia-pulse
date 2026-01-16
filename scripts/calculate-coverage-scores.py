#!/usr/bin/env python3
"""
Coverage Score Calculator v3 - CORRETO: POR PAÍS, POR SCOPE
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
print("COVERAGE SCORE CALCULATOR v3: POR PAÍS, POR SCOPE")
print("="*70)

# Calculate coverage_score_global POR PAÍS
print("\nCalculating coverage_score_global (per country)...")
cur.execute("""
    WITH country_sources AS (
        SELECT
            country_code,
            BOOL_OR(source = 'ACLED') as has_acled,
            BOOL_OR(source = 'WORLD_BANK') as has_worldbank,
            BOOL_OR(source = 'GDELT') as has_gdelt,
            MAX(event_time_start) as last_update
        FROM sofia.security_observations
        WHERE coverage_scope = 'global_comparable'
          AND country_code IS NOT NULL
        GROUP BY country_code
    ),
    scores AS (
        SELECT
            country_code,
            (CASE WHEN has_acled THEN 40 ELSE 0 END) +
            (CASE WHEN has_worldbank THEN 30 ELSE 0 END) +
            (CASE WHEN has_gdelt THEN 20 ELSE 0 END) +
            (CASE WHEN last_update >= CURRENT_DATE - INTERVAL '30 days' THEN 10 ELSE 0 END)
            as coverage_score
        FROM country_sources
    )
    UPDATE sofia.security_observations o
    SET coverage_score_global = s.coverage_score
    FROM scores s
    WHERE o.country_code = s.country_code
      AND o.coverage_scope = 'global_comparable'
""")

global_updated = cur.rowcount
print(f"Updated {global_updated:,} global coverage scores")

# Calculate coverage_score_local POR PAÍS (Brasil)
print("\nCalculating coverage_score_local (per country, local_only scope)...")
cur.execute("""
    WITH local_sources AS (
        SELECT
            country_code,
            BOOL_OR(source LIKE 'BRASIL_%') as has_gov_data,
            COUNT(DISTINCT source) as source_count,
            BOOL_OR(city IS NOT NULL) as has_city_granularity,
            MAX(event_time_start) as last_update
        FROM sofia.security_observations
        WHERE coverage_scope = 'local_only'
          AND country_code IS NOT NULL
        GROUP BY country_code
    ),
    scores AS (
        SELECT
            country_code,
            (CASE WHEN has_gov_data THEN 40 ELSE 0 END) +
            (CASE WHEN source_count >= 2 THEN 30 ELSE 0 END) +
            (CASE WHEN has_city_granularity THEN 20 ELSE 0 END) +
            (CASE WHEN last_update >= CURRENT_DATE - INTERVAL '90 days' THEN 10 ELSE 0 END)
            as coverage_score
        FROM local_sources
    )
    UPDATE sofia.security_observations o
    SET coverage_score_local = s.coverage_score
    FROM scores s
    WHERE o.country_code = s.country_code
      AND o.coverage_scope = 'local_only'
""")

local_updated = cur.rowcount
print(f"Updated {local_updated:,} local coverage scores")

# Summary POR PAÍS
print("\nCoverage Score Distribution (per country):")
cur.execute("""
    SELECT 
        CASE 
            WHEN coverage_score_global >= 75 THEN 'High (75-100)'
            WHEN coverage_score_global >= 50 THEN 'Medium (50-74)'
            WHEN coverage_score_global >= 30 THEN 'Low (30-49)'
            ELSE 'Very Low (0-29)'
        END as level,
        COUNT(DISTINCT country_code) as countries
    FROM sofia.security_observations
    WHERE coverage_scope = 'global_comparable'
      AND country_code IS NOT NULL
    GROUP BY level
    ORDER BY MIN(coverage_score_global) DESC
""")

for level, count in cur.fetchall():
    print(f"  {level:20} {count:,} countries")

# Show countries with low coverage (warning needed)
print("\nCountries with LOW coverage (< 50) - need warnings:")
cur.execute("""
    SELECT DISTINCT country_code, country_name, coverage_score_global
    FROM sofia.security_observations
    WHERE coverage_scope = 'global_comparable'
      AND coverage_score_global < 50
      AND country_code IS NOT NULL
    ORDER BY coverage_score_global ASC
    LIMIT 10
""")

for code, name, score in cur.fetchall():
    print(f"  {code} {name:30} score={score:.0f}")

cur.close()
conn.close()

print("\n" + "="*70)
print("COVERAGE SCORES UPDATED (Per Country, Per Scope)")
print("="*70)
