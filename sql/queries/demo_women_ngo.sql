-- ============================================================================
-- Women & NGO Intelligence - Queries de Demonstração + Auditoria
-- Execute estas queries diretamente no PostgreSQL para ver os dados
-- ============================================================================

-- ============================================================================
-- PARTE 1: DEMONSTRAÇÃO (CORRIGIDA - sem mascarar no_data)
-- ============================================================================

-- 1. TOP 10 PAÍSES - RISCO DE VIOLÊNCIA (SEM FILTRAR confidence)
-- Mostra flag quando confidence=0 para não mascarar países no_data
SELECT 
    country_code AS "País",
    violence_tier AS "Tier",
    violence_risk_score AS "Score Risco",
    events_30d AS "Eventos 4w",
    events_90d AS "Eventos 13w",
    fatalities_90d AS "Fatalidades 13w",
    data_scope AS "Escopo Dados",
    ROUND(confidence::numeric, 2) AS "Confiança",
    CASE WHEN confidence = 0 THEN '⚠ sem dados' ELSE '' END AS "Obs"
FROM sofia.mv_women_intelligence_by_country
ORDER BY violence_risk_score DESC
LIMIT 10;

-- 2. TOP 10 PAÍSES - COBERTURA NGO (SEM FILTRAR confidence)
SELECT 
    country_code AS "País",
    ngo_tier AS "Tier",
    ngo_coverage_score AS "Score Cobertura",
    ngo_signals_30d AS "Sinais 4w",
    ngo_signals_90d AS "Sinais 13w",
    sector_diversity AS "Diversidade Setores",
    ROUND(confidence::numeric, 2) AS "Confiança",
    CASE WHEN confidence = 0 THEN '⚠ sem dados' ELSE '' END AS "Obs"
FROM sofia.mv_ngo_coverage_by_country
ORDER BY ngo_coverage_score DESC
LIMIT 10;

-- 3. ESTATÍSTICAS GERAIS
SELECT 
    'Women Intelligence' AS domain,
    COUNT(*) AS total_countries,
    COUNT(*) FILTER (WHERE confidence > 0) AS countries_with_data,
    COUNT(*) FILTER (WHERE violence_tier = 'violence_crisis') AS crisis,
    COUNT(*) FILTER (WHERE violence_tier = 'violence_high') AS high_risk,
    COUNT(*) FILTER (WHERE violence_tier = 'violence_watch') AS watch,
    COUNT(*) FILTER (WHERE violence_tier = 'no_data') AS no_data
FROM sofia.mv_women_intelligence_by_country
UNION ALL
SELECT 
    'NGO Coverage' AS domain,
    COUNT(*) AS total_countries,
    COUNT(*) FILTER (WHERE confidence > 0) AS countries_with_data,
    COUNT(*) FILTER (WHERE ngo_tier = 'ngo_dense') AS dense,
    COUNT(*) FILTER (WHERE ngo_tier = 'ngo_active') AS active,
    COUNT(*) FILTER (WHERE ngo_tier = 'ngo_emerging') AS emerging,
    COUNT(*) FILTER (WHERE ngo_tier = 'no_data') AS no_data
FROM sofia.mv_ngo_coverage_by_country;

-- ============================================================================
-- PARTE 2: QUERIES DE AUDITORIA (detectar bugs/inconsistências)
-- ============================================================================

-- AUDITORIA 1: "Pega Mentiroso" - Score alto com events_30d=0
-- Se retornar muitos resultados, score está sendo puxado só por fatalities_90d
-- ou os weeks estão fora da janela "4 weeks" por formatação
SELECT 
    country_code AS "País",
    violence_tier AS "Tier",
    violence_risk_score AS "Score",
    events_30d AS "Eventos 4w",
    events_90d AS "Eventos 13w",
    fatalities_90d AS "Fatalidades 13w",
    ROUND(confidence::numeric, 2) AS "Conf",
    updated_at AS "Atualizado"
FROM sofia.mv_women_intelligence_by_country
WHERE confidence > 0
  AND events_30d = 0
  AND violence_risk_score >= 50
ORDER BY violence_risk_score DESC, fatalities_90d DESC
LIMIT 50;

-- AUDITORIA 2: Verificar alinhamento de weeks no ACLED
-- Se weeks_not_aligned > 0, os filtros date_trunc('week') não estão batendo
SELECT
    MIN(week) AS min_week,
    MAX(week) AS max_week,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE week <> date_trunc('week', week)) AS weeks_not_aligned,
    ROUND((COUNT(*) FILTER (WHERE week <> date_trunc('week', week))::numeric / COUNT(*)) * 100, 2) AS pct_not_aligned
FROM sofia.acled_aggregated;

-- AUDITORIA 2.1: Exemplos de weeks desalinhados (se houver)
SELECT 
    week AS week_original, 
    date_trunc('week', week) AS week_trunc,
    week - date_trunc('week', week) AS diferenca
FROM sofia.acled_aggregated
WHERE week <> date_trunc('week', week)
ORDER BY week DESC
LIMIT 20;

-- AUDITORIA 3: Quantos sinais NGO vs total sinais mapeados?
-- Justifica por que NGO Coverage é "raro" (não é bug, é dataset não-NGO-first)
WITH total_mapped AS (
    SELECT COUNT(*) AS total
    FROM sofia.industry_signals s
    JOIN sofia.signal_country_map m ON s.id = m.signal_id
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
),
ngo_mapped AS (
    SELECT COUNT(*) AS ngo
    FROM sofia.industry_signals s
    JOIN sofia.signal_country_map m ON s.id = m.signal_id
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
      AND (
          EXISTS (SELECT 1 FROM sofia.ngo_keyword_rules r
                  WHERE (r.field IN ('both','category') AND lower(COALESCE(s.category,'')) LIKE '%'||r.keyword||'%')
                     OR (r.field IN ('both','title') AND lower(COALESCE(s.title,'')) LIKE '%'||r.keyword||'%')
          )
      )
)
SELECT 
    ngo AS sinais_ngo,
    total AS sinais_total, 
    ROUND((ngo::numeric / NULLIF(total,0))*100, 2) AS ngo_pct
FROM ngo_mapped, total_mapped;

-- AUDITORIA 4: Quais keywords mais "disparam" NGO?
-- Útil para tuning futuro das regras
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
ORDER BY "Matches" DESC, r.keyword;

-- ============================================================================
-- PARTE 3: EXEMPLOS E VERIFICAÇÕES
-- ============================================================================

-- 5. EXEMPLO DE PAÍS ESPECÍFICO - BRASIL (BR)
SELECT 
    'Women Intelligence' AS domain,
    country_code,
    violence_tier AS tier,
    violence_risk_score AS score,
    events_30d,
    data_scope,
    confidence
FROM sofia.mv_women_intelligence_by_country
WHERE country_code = 'BR'
UNION ALL
SELECT 
    'NGO Coverage' AS domain,
    country_code,
    ngo_tier AS tier,
    ngo_coverage_score AS score,
    ngo_signals_30d AS events_30d,
    'ngo_deterministic' AS data_scope,
    confidence
FROM sofia.mv_ngo_coverage_by_country
WHERE country_code = 'BR';

-- 6. VERIFICAR IDEMPOTÊNCIA DOS ÍNDICES
SELECT 
    schemaname AS schema,
    tablename AS table,
    indexname AS index,
    indexdef AS definition
FROM pg_indexes
WHERE schemaname = 'sofia' 
  AND indexname IN ('idx_mv_women_intelligence_cc', 'idx_mv_ngo_coverage_cc', 'idx_ngo_keywords')
ORDER BY indexname;

-- 7. KEYWORDS NGO (Regras Determinísticas)
SELECT 
    keyword AS "Palavra-chave",
    field AS "Campo",
    weight AS "Peso"
FROM sofia.ngo_keyword_rules
ORDER BY weight DESC, keyword;
