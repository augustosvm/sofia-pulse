#!/usr/bin/env python3
"""
World Bank Normalizer - world_bank_data → security_observations
Structural indicators only (no geographic points)
"""
import psycopg2, os, json
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
print("WORLD BANK NORMALIZER: Structural Indicators")
print("="*70)

# Clear existing World Bank data
print("\nClearing existing World Bank data...")
cur.execute("DELETE FROM sofia.security_observations WHERE source = 'WORLD_BANK'")
print(f"Cleared {cur.rowcount:,} old records")

# Key structural indicators
STRUCTURAL_INDICATORS = {
    'SL.UEM.TOTL.ZS': 'Unemployment',
    'FP.CPI.TOTL.ZG': 'Inflation',
    'SI.POV.GINI': 'Gini Index',
    'PV.PER.RNK': 'Political Stability',
    'RL.PER.RNK': 'Rule of Law',
    'GE.PER.RNK': 'Government Effectiveness'
}

# Check if world_bank_data table exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' AND table_name = 'world_bank_data'
    )
""")

if not cur.fetchone()[0]:
    print("\nWARNING: sofia.world_bank_data table does not exist")
    print("Skipping World Bank normalization")
    cur.close()
    conn.close()
    exit(0)

# Insert World Bank structural data
print("\nNormalizing World Bank data...")

for indicator_code, indicator_name in STRUCTURAL_INDICATORS.items():
    cur.execute(f"""
        INSERT INTO sofia.security_observations (
            source,
            source_id,
            signal_type,
            coverage_scope,
            country_code,
            country_name,
            latitude,
            longitude,
            severity_raw,
            severity_norm,
            confidence_score,
            coverage_score_global,
            coverage_score_local,
            event_time_start,
            event_time_end,
            event_count,
            fatalities,
            raw_payload,
            collected_at
        )
        SELECT
            'WORLD_BANK' as source,
            country_code || '_' || '{indicator_code}' || '_' || year::text as source_id,
            'structural' as signal_type,
            'global_comparable' as coverage_scope,
            country_code,
            country_name,
            NULL as latitude,  -- Structural data has no geographic point
            NULL as longitude,
            value as severity_raw,
            LEAST(100, value) as severity_norm,  -- Simplified normalization
            95.0 as confidence_score,  -- World Bank is very high quality
            80.0 as coverage_score_global,
            0.0 as coverage_score_local,
            make_date(year, 1, 1) as event_time_start,
            make_date(year, 12, 31) as event_time_end,
            1 as event_count,
            0 as fatalities,
            jsonb_build_object(
                'indicator_code', '{indicator_code}',
                'indicator_name', '{indicator_name}',
                'year', year,
                'value', value
            ) as raw_payload,
            CURRENT_TIMESTAMP
        FROM sofia.world_bank_data
        WHERE indicator_code = '{indicator_code}'
          AND year >= EXTRACT(YEAR FROM CURRENT_DATE) - 5  -- Last 5 years
          AND value IS NOT NULL
        ON CONFLICT (source_id) DO NOTHING
    """)
    
    print(f"  {indicator_name}: {cur.rowcount:,} records")

# Verify
cur.execute("""
    SELECT COUNT(*), COUNT(DISTINCT country_code)
    FROM sofia.security_observations
    WHERE source = 'WORLD_BANK'
""")
total, countries = cur.fetchone()
print(f"\nVerification:")
print(f"  Total: {total:,} observations")
print(f"  Countries: {countries}")

cur.close()
conn.close()

print("\n" + "="*70)
print("WORLD BANK NORMALIZATION COMPLETE")
print("="*70)
