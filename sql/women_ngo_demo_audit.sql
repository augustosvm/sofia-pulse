-- ============================================================================
-- Women & NGO Intelligence - Demonstração + Auditoria
-- Execute: psql -f sql/women_ngo_demo_audit.sql
-- ============================================================================

-- ============================================================================
-- DEMONSTRAÇÃO (sem mascarar no_data)
-- ============================================================================

-- 1. TOP 10 PAÍSES - RISCO DE VIOLÊNCIA
SELECT
    country_code AS "Pais",
    violence_tier AS "Tier",
    violence_risk_score AS "Score",
    events_30d AS "Eventos 4w",
    events_90d AS "Eventos 13w",
    fatalities_90d AS "Fatal 13w",
    ROUND(confidence::numeric, 2) AS "Conf",
    CASE WHEN confidence = 0 THEN 'sem_dados' ELSE '' END AS "Obs"
FROM sofia.mv_women_intelligence_by_country
ORDER BY violence_risk_score DESC
LIMIT 10;

-- 2. TOP 10 PAÍSES - COBERTURA NGO
SELECT
    country_code AS "Pais",
    ngo_tier AS "Tier",
    ngo_coverage_score AS "Score",
    ngo_signals_30d AS "Sinais 4w",
    ngo_signals_90d AS "Sinais 13w",
    ROUND(confidence::numeric, 2) AS "Conf",
    CASE WHEN confidence = 0 THEN 'sem_dados' ELSE '' END AS "Obs"
FROM sofia.mv_ngo_coverage_by_country
ORDER BY ngo_coverage_score DESC
LIMIT 10;

-- 3. ESTATÍSTICAS GERAIS (usando confidence=0 para no_data)
SELECT
    'Women Intelligence' AS domain,
    COUNT(*) AS total_countries,
    COUNT(*) FILTER (WHERE confidence > 0) AS with_data,
    COUNT(*) FILTER (WHERE violence_tier = 'violence_crisis') AS crisis,
    COUNT(*) FILTER (WHERE violence_tier = 'violence_high') AS high,
    COUNT(*) FILTER (WHERE violence_tier = 'violence_watch') AS watch,
    COUNT(*) FILTER (WHERE confidence = 0) AS no_data
FROM sofia.mv_women_intelligence_by_country
UNION ALL
SELECT
    'NGO Coverage' AS domain,
    COUNT(*) AS total_countries,
    COUNT(*) FILTER (WHERE confidence > 0) AS with_data,
    COUNT(*) FILTER (WHERE ngo_tier = 'ngo_dense') AS dense,
    COUNT(*) FILTER (WHERE ngo_tier = 'ngo_active') AS active,
    COUNT(*) FILTER (WHERE ngo_tier = 'ngo_emerging') AS emerging,
    COUNT(*) FILTER (WHERE confidence = 0) AS no_data
FROM sofia.mv_ngo_coverage_by_country;

-- ============================================================================
-- AUDITORIAS (detectar inconsistências)
-- ============================================================================

-- AUDITORIA 1: Score alto com events_30d=0 (componentes do score)
SELECT
    country_code AS "Pais",
    violence_tier AS "Tier",
    violence_risk_score AS "Score_Total",
    events_30d AS "Eventos_4w",
    fatalities_90d AS "Fatal_13w",
    (events_30d * 2) AS "Score_Events",
    ROUND((fatalities_90d * 0.5)::numeric, 1) AS "Score_Fatal",
    ROUND(((events_30d * 2 + fatalities_90d * 0.5)::numeric / 10), 2) AS "Score_Bruto",
    ROUND(confidence::numeric, 2) AS "Conf"
FROM sofia.mv_women_intelligence_by_country
WHERE confidence > 0
  AND events_30d = 0
  AND violence_risk_score >= 50
ORDER BY violence_risk_score DESC
LIMIT 20;

-- AUDITORIA 2: Alinhamento de weeks ACLED (versao enterprise com distinct weeks)
-- Se weeks_not_aligned > 0, tem bug na base
-- Se distinct_weeks_not_aligned > 0, precisa migration 017c
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT week) AS distinct_weeks,
    COUNT(*) FILTER (WHERE week <> date_trunc('week', week)) AS rows_not_aligned,
    COUNT(DISTINCT week) FILTER (WHERE week <> date_trunc('week', week)) AS distinct_weeks_not_aligned,
    ROUND((COUNT(*) FILTER (WHERE week <> date_trunc('week', week))::numeric / NULLIF(COUNT(*),0)) * 100, 2) AS pct_rows_not_aligned,
    ROUND((COUNT(DISTINCT week) FILTER (WHERE week <> date_trunc('week', week))::numeric / NULLIF(COUNT(DISTINCT week),0)) * 100, 2) AS pct_distinct_weeks_not_aligned
FROM sofia.acled_aggregated;

-- AUDITORIA 2.1: Exemplos de weeks desalinhados (max 20 distinct weeks)
SELECT DISTINCT
    week AS week_original,
    date_trunc('week', week) AS week_aligned,
    week - date_trunc('week', week) AS offset
FROM sofia.acled_aggregated
WHERE week <> date_trunc('week', week)
ORDER BY week DESC
LIMIT 20;

-- AUDITORIA 3: NGO sinais raw vs mapped (detecta backfill incompleto)
WITH ngo_raw AS (
    SELECT COUNT(*) AS ngo_raw
    FROM sofia.industry_signals s
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
      AND EXISTS (
          SELECT 1
          FROM sofia.ngo_keyword_rules r
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
          SELECT 1
          FROM sofia.ngo_keyword_rules r
          WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
             OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
      )
)
SELECT
    ngo_raw AS sinais_ngo_raw,
    ngo_mapped AS sinais_ngo_mapped,
    ROUND((ngo_mapped::numeric / NULLIF(ngo_raw,0))*100, 2) AS pct_mapped
FROM ngo_raw, ngo_mapped;

-- AUDITORIA 3.1: NGO hits sem mapeamento geográfico (unmapped signals)
-- Se pct_unmapped > 0, o problema é signal_country_map (backfill/geo)
WITH ngo_hits AS (
    SELECT DISTINCT s.id
    FROM sofia.industry_signals s
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
      AND EXISTS (
          SELECT 1
          FROM sofia.ngo_keyword_rules r
          WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
             OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
      )
)
SELECT
    COUNT(*) AS ngo_hits_total,
    COUNT(*) FILTER (WHERE m.signal_id IS NULL) AS ngo_hits_unmapped,
    ROUND((COUNT(*) FILTER (WHERE m.signal_id IS NULL)::numeric / NULLIF(COUNT(*),0)) * 100, 2) AS pct_unmapped
FROM ngo_hits h
LEFT JOIN sofia.signal_country_map m ON m.signal_id = h.id;

-- AUDITORIA 3.1b: Exemplos de NGO hits unmapped (para debugar rápido)
-- Lista os sinais NGO que existem mas nao tem geo (max 50)
WITH ngo_hits AS (
    SELECT DISTINCT s.id
    FROM sofia.industry_signals s
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
      AND EXISTS (
          SELECT 1
          FROM sofia.ngo_keyword_rules r
          WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
             OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
      )
),
unmapped AS (
    SELECT h.id AS signal_id
    FROM ngo_hits h
    LEFT JOIN sofia.signal_country_map m ON m.signal_id = h.id
    WHERE m.signal_id IS NULL
)
SELECT
    s.id,
    s.published_at,
    COALESCE(s.source,'') AS source,
    COALESCE(s.url,'') AS url,
    COALESCE(s.category,'') AS category,
    COALESCE(s.title,'') AS title
FROM sofia.industry_signals s
JOIN unmapped u ON u.signal_id = s.id
ORDER BY s.published_at DESC
LIMIT 50;

-- AUDITORIA 3.1c: Heurística simples - sinais unmapped que mencionam pais no titulo
-- (serve pra provar que o pipeline falhou, nao que o mundo nao tem dado)
WITH ngo_hits AS (
    SELECT DISTINCT s.id
    FROM sofia.industry_signals s
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
      AND EXISTS (
          SELECT 1
          FROM sofia.ngo_keyword_rules r
          WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
             OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
      )
),
unmapped AS (
    SELECT h.id AS signal_id
    FROM ngo_hits h
    LEFT JOIN sofia.signal_country_map m ON m.signal_id = h.id
    WHERE m.signal_id IS NULL
)
SELECT
    s.id,
    s.published_at,
    s.title
FROM sofia.industry_signals s
JOIN unmapped u ON u.signal_id = s.id
WHERE lower(COALESCE(s.title,'')) ~ '(brazil|brasil|germany|deutschland|france|china|india|ukraine|israel|gaza|iran|russia|usa|united states)'
ORDER BY s.published_at DESC
LIMIT 50;


-- AUDITORIA 4: Keywords NGO ranqueadas por frequencia
SELECT
    r.keyword AS "Keyword",
    r.field AS "Campo",
    COUNT(*) AS "Matches"
FROM sofia.ngo_keyword_rules r
JOIN sofia.industry_signals s ON (
       (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
    OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
)
WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
GROUP BY r.keyword, r.field
ORDER BY "Matches" DESC;
