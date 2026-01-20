#!/usr/bin/env python3
"""
ACLED Normalizer v2 - CORRETO conforme matriz de normalização
severity_norm = P95 percentile normalization
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
print("ACLED NORMALIZER v2: P95 Percentile Normalization")
print("="*70)

# Clear existing
print("\nClearing existing ACLED data...")
cur.execute("DELETE FROM sofia.security_observations WHERE source = 'ACLED'")
print(f"Cleared {cur.rowcount:,} old records")

# Insert with P95 normalization
print("\nNormalizing ACLED data (P95 percentile)...")
cur.execute("""
    WITH severity_calc AS (
        SELECT
            source_id,
            country_name,
            admin1,
            city,
            latitude,
            longitude,
            event_date,
            event_count,
            fatalities,
            raw_payload,
            -- severity_raw = events + (fatalities * 3)
            (event_count + (COALESCE(fatalities, 0) * 3.0)) as severity_raw
        FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
    ),
    p95_calc AS (
        SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY severity_raw) as p95
        FROM severity_calc
    )
    INSERT INTO sofia.security_observations (
        source,
        source_id,
        signal_type,
        coverage_scope,
        country_code,
        country_name,
        admin1,
        city,
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
        'ACLED' as source,
        s.source_id,
        'acute' as signal_type,
        'global_comparable' as coverage_scope,
        NULL as country_code,
        s.country_name,
        s.admin1,
        s.city,
        s.latitude,
        s.longitude,
        s.severity_raw,
        -- severity_norm = 100 * (severity_raw / P95) LIMIT 100
        LEAST(100, 100 * (s.severity_raw / NULLIF(p.p95, 0))) as severity_norm,
        90.0 as confidence_score,
        40.0 as coverage_score_global,  -- Base: ACLED presente
        0.0 as coverage_score_local,
        s.event_date as event_time_start,
        s.event_date as event_time_end,
        s.event_count,
        s.fatalities,
        s.raw_payload,
        CURRENT_TIMESTAMP
    FROM severity_calc s
    CROSS JOIN p95_calc p
""")

inserted = cur.rowcount
print(f"OK Inserted {inserted:,} ACLED observations")

# Update country codes
print("\nUpdating country codes...")
cur.execute("""
    UPDATE sofia.security_observations
    SET country_code = c.country_code_iso2
    FROM sofia.dim_country AS c
    WHERE sofia.security_observations.source = 'ACLED'
      AND sofia.security_observations.country_code IS NULL
      AND LOWER(sofia.security_observations.country_name) = LOWER(c.country_name_en)
""")
print(f"Updated {cur.rowcount:,} country codes")

# Update coverage scores (ACLED=40, recency bonus)
print("\nUpdating coverage scores...")
cur.execute("""
    UPDATE sofia.security_observations
    SET coverage_score_global = 
        40 +  -- ACLED presente
        CASE 
            WHEN event_time_start >= CURRENT_DATE - INTERVAL '30 days' THEN 10
            ELSE 0
        END
    WHERE source = 'ACLED'
""")
print(f"Updated {cur.rowcount:,} coverage scores")

# Verify
cur.execute("""
    SELECT COUNT(*), COUNT(DISTINCT country_name),
           MIN(severity_norm), MAX(severity_norm), AVG(severity_norm)
    FROM sofia.security_observations
    WHERE source = 'ACLED'
""")
total, countries, min_sev, max_sev, avg_sev = cur.fetchone()
print(f"\nVerification:")
print(f"  Total: {total:,} observations")
print(f"  Countries: {countries}")
print(f"  Severity range: {min_sev:.2f} - {max_sev:.2f} (avg: {avg_sev:.2f})")

cur.close()
conn.close()

print("\n" + "="*70)
print("ACLED NORMALIZATION COMPLETE (P95 Method)")
print("="*70)
