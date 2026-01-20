#!/usr/bin/env python3
"""
ACLED Normalizer v3 - ROBUSTO com Alias Mapping
Normalização P95 + mapeamento de country_code via dim_country_alias
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
print("ACLED NORMALIZER v3: P95 + Robust Country Mapping")
print("="*70)

# Clear existing
print("\n🧹 Limpando dados ACLED antigos...")
cur.execute("DELETE FROM sofia.security_observations WHERE source = 'ACLED'")
print(f"   Removidos {cur.rowcount:,} registros antigos")

# Insert with P95 normalization + ROBUST country_code mapping
print("\n🔄 Normalizando ACLED com mapeamento robusto...")
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
    ),
    country_mapping AS (
        SELECT DISTINCT ON (s.country_name)
            s.country_name,
            COALESCE(
                -- Tenta alias exato (case-insensitive)
                (SELECT country_code_iso2 FROM sofia.dim_country_alias 
                 WHERE LOWER(alias_text) = LOWER(s.country_name) 
                 LIMIT 1),
                -- Fallback: tenta country_name_en direto
                (SELECT country_code_iso2 FROM sofia.dim_country 
                 WHERE LOWER(country_name_en) = LOWER(s.country_name) 
                 LIMIT 1)
            ) as country_code
        FROM severity_calc s
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
        cm.country_code,
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
    LEFT JOIN country_mapping cm ON s.country_name = cm.country_name
""")

inserted = cur.rowcount
print(f"   ✅ Inseridos {inserted:,} registros ACLED")

# Update coverage scores (recency bonus)
print("\n📊 Atualizando coverage scores...")
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
print(f"   Atualizados {cur.rowcount:,} scores")

# Verify
print("\n✅ VERIFICAÇÃO:")
cur.execute("""
    SELECT COUNT(*), COUNT(country_code), COUNT(DISTINCT country_name),
           MIN(severity_norm), MAX(severity_norm), AVG(severity_norm)
    FROM sofia.security_observations
    WHERE source = 'ACLED'
""")
total, with_code, countries, min_sev, max_sev, avg_sev = cur.fetchone()
print(f"   Total: {total:,} observações")
print(f"   Com country_code: {with_code:,} ({with_code/total*100:.1f}%)")
print(f"   Países distintos: {countries}")
print(f"   Severity: {min_sev:.2f} - {max_sev:.2f} (média: {avg_sev:.2f})")

# Check NULL country_codes
cur.execute("""
    SELECT COUNT(*) FROM sofia.security_observations
    WHERE source='ACLED' AND country_code IS NULL
""")
null_count = cur.fetchone()[0]
if null_count > 0:
    print(f"\n⚠️  {null_count:,} registros SEM country_code")
    cur.execute("""
        SELECT country_name, COUNT(*) as cnt
        FROM sofia.security_observations
        WHERE source='ACLED' AND country_code IS NULL
        GROUP BY country_name
        ORDER BY cnt DESC
        LIMIT 10
    """)
    print("   Top 10 países sem match:")
    for name, cnt in cur.fetchall():
        print(f"     - {name}: {cnt:,}")

# Sample LATAM countries
print("\n🌎 Amostra América Latina:")
cur.execute("""
    SELECT country_code, country_name, COUNT(*) as cnt
    FROM sofia.security_observations
    WHERE source='ACLED' 
      AND country_code IN ('BR','AR','CL','CO','PE','VE','BO','EC','PY','UY','MX')
    GROUP BY country_code, country_name
    ORDER BY cnt DESC
""")
latam_found = False
for code, name, cnt in cur.fetchall():
    latam_found = True
    print(f"   {code} - {name}: {cnt:,}")
if not latam_found:
    print("   ❌ Nenhum país LATAM encontrado")

cur.close()
conn.close()

print("\n" + "="*70)
print("ACLED NORMALIZATION COMPLETE (v3 - Robust Mapping)")
print("="*70)
