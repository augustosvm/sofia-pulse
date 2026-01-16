#!/usr/bin/env python3
"""
GDELT Normalizer v3 - CORRETO com Z-score POR PAÍS e POR JANELA
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
print("GDELT NORMALIZER v3: Z-Score POR PAÍS e POR JANELA")
print("="*70)

# Clear existing
print("\nClearing existing GDELT data...")
cur.execute("DELETE FROM sofia.security_observations WHERE source = 'GDELT'")
print(f"Cleared {cur.rowcount:,} old records")

# Check source
cur.execute("SELECT COUNT(*) FROM sofia.gdelt_events WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'")
source_count = cur.fetchone()[0]
print(f"\nSource: {source_count:,} GDELT events (last 90 days)")

if source_count == 0:
    print("No GDELT data to normalize")
    cur.close()
    conn.close()
    exit(0)

# Insert with Z-score POR PAÍS e POR JANELA
print("\nNormalizing GDELT data (Z-score per country, 30-day window)...")
cur.execute("""
    WITH windowed_counts AS (
        SELECT
            action_geo_country,
            DATE_TRUNC('day', event_date) as day,
            COUNT(*) as daily_count
        FROM sofia.gdelt_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
          AND action_geo_country IS NOT NULL
        GROUP BY action_geo_country, DATE_TRUNC('day', event_date)
    ),
    country_stats AS (
        SELECT
            action_geo_country,
            AVG(daily_count) as mean_count,
            STDDEV(daily_count) as stddev_count
        FROM windowed_counts
        WHERE day >= CURRENT_DATE - INTERVAL '30 days'  -- Janela de 30 dias
        GROUP BY action_geo_country
    ),
    recent_events AS (
        SELECT
            e.global_event_id,
            e.action_geo_country,
            e.action_geo_lat,
            e.action_geo_lon,
            e.event_date,
            e.goldstein_scale,
            e.avg_tone,
            e.num_mentions,
            e.num_articles,
            e.actor1_name,
            e.actor2_name,
            e.ingested_at,
            -- Z-score POR PAÍS com fallback para stddev=0
            CASE 
                WHEN cs.stddev_count > 0.001 THEN  -- Epsilon para evitar divisão por zero
                    (wc.daily_count - cs.mean_count) / cs.stddev_count
                ELSE 0  -- Fallback: país com variação zero = sem momentum
            END as zscore_per_country
        FROM sofia.gdelt_events e
        JOIN windowed_counts wc 
            ON e.action_geo_country = wc.action_geo_country 
            AND DATE_TRUNC('day', e.event_date) = wc.day
        JOIN country_stats cs 
            ON e.action_geo_country = cs.action_geo_country
        WHERE e.event_date >= CURRENT_DATE - INTERVAL '90 days'
          AND e.action_geo_lat IS NOT NULL
          AND e.action_geo_lon IS NOT NULL
    )
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
        'GDELT' as source,
        global_event_id as source_id,
        'acute' as signal_type,
        'global_comparable' as coverage_scope,
        action_geo_country as country_code,
        NULL as country_name,
        action_geo_lat as latitude,
        action_geo_lon as longitude,
        ABS(zscore_per_country) as severity_raw,
        -- severity_norm = clamp(abs(zscore_per_country) * 20, 0, 100)
        LEAST(100, GREATEST(0, ABS(COALESCE(zscore_per_country, 0)) * 20)) as severity_norm,
        70.0 as confidence_score,
        0.0 as coverage_score_global,  -- Will be calculated per country
        0.0 as coverage_score_local,
        event_date as event_time_start,
        event_date as event_time_end,
        1 as event_count,
        0 as fatalities,
        jsonb_build_object(
            'global_event_id', global_event_id,
            'goldstein_scale', goldstein_scale,
            'avg_tone', avg_tone,
            'num_mentions', num_mentions,
            'num_articles', num_articles,
            'actor1_name', actor1_name,
            'actor2_name', actor2_name,
            'zscore_per_country', zscore_per_country,
            'interpretation', 'momentum_per_country'
        ) as raw_payload,
        ingested_at
    FROM recent_events
""")

inserted = cur.rowcount
print(f"OK Inserted {inserted:,} GDELT observations")

# Update country names
print("\nUpdating country names...")
cur.execute("""
    UPDATE sofia.security_observations o
    SET country_name = c.name
    FROM sofia.dim_country c
    WHERE o.source = 'GDELT'
      AND o.country_name IS NULL
      AND o.country_code = c.iso_alpha2
""")
print(f"Updated {cur.rowcount:,} country names")

# Verify
cur.execute("""
    SELECT COUNT(*), COUNT(DISTINCT country_code),
           MIN(severity_norm), MAX(severity_norm), AVG(severity_norm)
    FROM sofia.security_observations
    WHERE source = 'GDELT'
""")
total, countries, min_sev, max_sev, avg_sev = cur.fetchone()
print(f"\nVerification:")
print(f"  Total: {total:,} observations")
print(f"  Countries: {countries}")
print(f"  Severity range: {min_sev:.2f} - {max_sev:.2f} (avg: {avg_sev:.2f})")

cur.close()
conn.close()

print("\n" + "="*70)
print("GDELT NORMALIZATION COMPLETE (Per-Country Z-Score)")
print("="*70)
