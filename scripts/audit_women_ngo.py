#!/usr/bin/env python3
"""
Women & NGO Intelligence - Script de Auditoria
Execute: python scripts/audit_women_ngo.py
"""
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

print("=" * 80)
print("AUDITORIA 1: Score Alto com events_30d=0 (Componentes do Score)")
print("=" * 80)

cur = conn.cursor(cursor_factory=DictCursor)
cur.execute("""
    SELECT 
        country_code,
        violence_tier,
        violence_risk_score,
        events_30d,
        fatalities_90d,
        (events_30d * 2) AS score_from_events,
        ROUND((fatalities_90d * 0.5)::numeric, 1) AS score_from_fatalities,
        confidence
    FROM sofia.mv_women_intelligence_by_country
    WHERE confidence > 0 AND events_30d = 0 AND violence_risk_score >= 50
    ORDER BY violence_risk_score DESC
    LIMIT 10
""")
rows = cur.fetchall()
print(f"\nTotal: {len(rows)} países com score >= 50 mas events_30d = 0")
print("\nTop 5:")
for r in rows[:5]:
    print(f"  {r['country_code']}: tier={r['violence_tier']}, " +
          f"score={r['violence_risk_score']} (events={r['score_from_events']}, " +
          f"fatal={r['score_from_fatalities']}), conf={r['confidence']}")

audit1_has_issues = len(rows) > 0

print("\n" + "=" * 80)
print("AUDITORIA 2: Alinhamento de Weeks ACLED")
print("=" * 80)

cur.execute("""
    SELECT 
        MIN(week) AS min_week,
        MAX(week) AS max_week,
        COUNT(*) AS total_rows,
        COUNT(*) FILTER (WHERE week <> date_trunc('week', week)) AS weeks_not_aligned
    FROM sofia.acled_aggregated
""")
r = cur.fetchone()
print(f"\nMin: {r['min_week']}")
print(f"Max: {r['max_week']}")
print(f"Total rows: {r['total_rows']}")
print(f"Weeks desalinhados: {r['weeks_not_aligned']}")

weeks_aligned = r['weeks_not_aligned'] == 0
if not weeks_aligned:
    pct = (r['weeks_not_aligned'] / r['total_rows']) * 100
    print(f"% Desalinhamento: {pct:.2f}%")

print("\n" + "=" * 80)
print("AUDITORIA 3: NGO Sinais Raw vs Mapped (Backfill Check)")
print("=" * 80)

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
print(f"\nSinais NGO (raw): {r['ngo_raw']}")
print(f"Sinais NGO (mapped): {r['ngo_mapped']}")
print(f"% Mapeado: {r['pct_mapped']}%")

ngo_mapping_ok = r['pct_mapped'] > 80 if r['ngo_raw'] > 0 else True

print("\n" + "=" * 80)
print("AUDITORIA 4: Keywords NGO Mais Frequentes")
print("=" * 80)

cur.execute("""
    SELECT r.keyword, r.field, COUNT(*) AS matches
    FROM sofia.ngo_keyword_rules r
    JOIN sofia.industry_signals s ON (
           (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
        OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
    )
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
    GROUP BY r.keyword, r.field
    ORDER BY matches DESC
    LIMIT 10
""")
rows = cur.fetchall()
print("\nTop 10 keywords:")
for r in rows:
    print(f"  {r['keyword']} ({r['field']}): {r['matches']} matches")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("RESUMO DAS AUDITORIAS")
print("=" * 80)

if audit1_has_issues:
    print("\n1. ENCONTRADO: Países com score alto mas events_30d=0")
    print("   - Score está sendo puxado por fatalities_90d")
    print("   - Tecnicamente correto, mas pode confundir (tier=no_data com score alto)")
else:
    print("\n1. OK: Nenhum país com score alto e events_30d=0")

if weeks_aligned:
    print("\n2. OK: Weeks estão alinhados (0 desalinhamentos)")
else:
    print("\n2. PROBLEMA: Weeks desalinhados detectados")
    print("   - Filtros date_trunc('week') podem estar incorretos")

if ngo_mapping_ok:
    print("\n3. OK: NGO sinais bem mapeados")
else:
    print("\n3. ALERTA: NGO sinais com baixo mapeamento")
    print("   - Considere revisar backfill do signal_country_map")

print("\n4. OK: Keywords NGO identificadas e ranqueadas")
