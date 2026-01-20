#!/usr/bin/env python3
"""Execute diagnostic queries for Women/NGO Intelligence."""
import psycopg2
from psycopg2.extras import DictCursor
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
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    dbname=os.getenv("POSTGRES_DB", "sofia_db"),
    connect_timeout=10,
    sslmode=os.getenv("POSTGRES_SSLMODE", "prefer")
)

cur = conn.cursor(cursor_factory=DictCursor)

print("DIAGNOSTICOS PARA DECISAO:")
print("=" * 60)

# Auditoria 2
cur.execute("""
    SELECT 
        COUNT(*) AS total_rows,
        COUNT(DISTINCT week) AS distinct_weeks,
        COUNT(*) FILTER (WHERE week <> date_trunc('week', week)) AS rows_not_aligned,
        COUNT(DISTINCT week) FILTER (WHERE week <> date_trunc('week', week)) AS distinct_weeks_not_aligned
    FROM sofia.acled_aggregated
""")
r = cur.fetchone()
print(f"\nAUDITORIA 2 (week alignment):")
print(f"  total_rows: {r['total_rows']}")
print(f"  distinct_weeks: {r['distinct_weeks']}")
print(f"  rows_not_aligned: {r['rows_not_aligned']}")
print(f"  distinct_weeks_not_aligned: {r['distinct_weeks_not_aligned']}")

# Auditoria 3
cur.execute("""
    WITH ngo_raw AS (
        SELECT COUNT(*) AS ngo_raw
        FROM sofia.industry_signals s
        WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
          AND EXISTS (
              SELECT 1 FROM sofia.ngo_keyword_rules r
              WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
                 OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
          )
    ),
    ngo_mapped AS (
        SELECT COUNT(*) AS ngo_mapped
        FROM sofia.industry_signals s
        JOIN sofia.signal_country_map m ON s.id = m.signal_id
        WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
          AND EXISTS (
              SELECT 1 FROM sofia.ngo_keyword_rules r
              WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
                 OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
          )
    )
    SELECT ngo_raw, ngo_mapped, ROUND((ngo_mapped::numeric / NULLIF(ngo_raw,0))*100, 2) AS pct_mapped
    FROM ngo_raw, ngo_mapped
""")
r = cur.fetchone()
print(f"\nAUDITORIA 3:")
print(f"  ngo_raw: {r['ngo_raw']}")
print(f"  ngo_mapped: {r['ngo_mapped']}")
print(f"  pct_mapped: {r['pct_mapped']}%")

# Auditoria 3.1
cur.execute("""
    WITH ngo_hits AS (
        SELECT DISTINCT s.id
        FROM sofia.industry_signals s
        WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
          AND EXISTS (
              SELECT 1 FROM sofia.ngo_keyword_rules r
              WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
                 OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
          )
    )
    SELECT
        COUNT(*) AS ngo_hits_total,
        COUNT(*) FILTER (WHERE m.signal_id IS NULL) AS ngo_hits_unmapped,
        ROUND((COUNT(*) FILTER (WHERE m.signal_id IS NULL)::numeric / NULLIF(COUNT(*),0)) * 100, 2) AS pct_unmapped
    FROM ngo_hits h
    LEFT JOIN sofia.signal_country_map m ON m.signal_id = h.id
""")
r = cur.fetchone()
print(f"\nAUDITORIA 3.1:")
print(f"  ngo_hits_total: {r['ngo_hits_total']}")
print(f"  ngo_hits_unmapped: {r['ngo_hits_unmapped']}")
print(f"  pct_unmapped: {r['pct_unmapped']}%")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("Copie esses 3 grupos de numeros para o usuario.")
