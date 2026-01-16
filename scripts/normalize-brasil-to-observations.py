#!/usr/bin/env python3
"""
Brasil Normalizer - brazil_security_data → security_observations
Local high-resolution data (NOT globally comparable)
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
print("BRASIL NORMALIZER: Local High-Resolution Data")
print("="*70)

# Clear existing Brasil data
print("\nClearing existing Brasil data...")
cur.execute("DELETE FROM sofia.security_observations WHERE source LIKE 'BRASIL_%'")
print(f"Cleared {cur.rowcount:,} old records")

# Check if brazil_security_data table exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' AND table_name = 'brazil_security_data'
    )
""")

if not cur.fetchone()[0]:
    print("\nWARNING: sofia.brazil_security_data table does not exist")
    print("Skipping Brasil normalization")
    cur.close()
    conn.close()
    exit(0)

# Insert Brasil crime data
print("\nNormalizing Brasil crime data...")
cur.execute("""
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
        'BRASIL_CRIME' as source,
        'BR_' || state || '_' || year::text as source_id,
        'local' as signal_type,
        'local_only' as coverage_scope,
        'BR' as country_code,
        'Brazil' as country_name,
        state as admin1,
        NULL as city,
        NULL as latitude,  -- State-level data
        NULL as longitude,
        homicide_rate + robbery_rate as severity_raw,
        LEAST(100, (homicide_rate + robbery_rate) / 2.0) as severity_norm,
        85.0 as confidence_score,
        0.0 as coverage_score_global,  -- Local only
        90.0 as coverage_score_local,
        make_date(year, 1, 1) as event_time_start,
        make_date(year, 12, 31) as event_time_end,
        1 as event_count,
        COALESCE(homicides, 0) as fatalities,
        jsonb_build_object(
            'state', state,
            'year', year,
            'homicide_rate', homicide_rate,
            'robbery_rate', robbery_rate,
            'source_type', 'state_crime'
        ) as raw_payload,
        CURRENT_TIMESTAMP
    FROM sofia.brazil_security_data
    WHERE year >= EXTRACT(YEAR FROM CURRENT_DATE) - 3
      AND homicide_rate IS NOT NULL
    ON CONFLICT (source_id) DO NOTHING
""")

crime_inserted = cur.rowcount
print(f"OK Inserted {crime_inserted:,} crime observations")

# Check if women violence data exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'sofia' AND table_name = 'brazil_women_violence'
    )
""")

if cur.fetchone()[0]:
    print("\nNormalizing Brasil violence against women data...")
    cur.execute("""
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
            'BRASIL_VIOLENCE_WOMEN' as source,
            'BR_WOMEN_' || state || '_' || year::text as source_id,
            'local' as signal_type,
            'local_only' as coverage_scope,
            'BR' as country_code,
            'Brazil' as country_name,
            state as admin1,
            NULL as city,
            NULL as latitude,
            NULL as longitude,
            femicide_rate as severity_raw,
            LEAST(100, femicide_rate * 10) as severity_norm,
            85.0 as confidence_score,
            0.0 as coverage_score_global,
            90.0 as coverage_score_local,
            make_date(year, 1, 1) as event_time_start,
            make_date(year, 12, 31) as event_time_end,
            1 as event_count,
            COALESCE(femicides, 0) as fatalities,
            jsonb_build_object(
                'state', state,
                'year', year,
                'femicide_rate', femicide_rate,
                'source_type', 'women_violence'
            ) as raw_payload,
            CURRENT_TIMESTAMP
        FROM sofia.brazil_women_violence
        WHERE year >= EXTRACT(YEAR FROM CURRENT_DATE) - 3
          AND femicide_rate IS NOT NULL
        ON CONFLICT (source_id) DO NOTHING
    """)
    
    women_inserted = cur.rowcount
    print(f"OK Inserted {women_inserted:,} violence against women observations")

# Verify
cur.execute("""
    SELECT source, COUNT(*)
    FROM sofia.security_observations
    WHERE source LIKE 'BRASIL_%'
    GROUP BY source
""")

print(f"\nVerification:")
for source, count in cur.fetchall():
    print(f"  {source}: {count:,} observations")

cur.close()
conn.close()

print("\n" + "="*70)
print("BRASIL NORMALIZATION COMPLETE")
print("="*70)
print("\nWARNING: Brasil data is LOCAL ONLY - not globally comparable")
