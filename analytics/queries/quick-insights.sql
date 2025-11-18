-- Sofia Pulse - Quick Insights (SQL apenas, sem IA)
-- Execute: psql -U sofia -d sofia_db -f analytics/queries/quick-insights.sql

\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo '📊 Sofia Pulse - Quick Insights Dashboard'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

\echo ''
\echo '📈 1. PERFORMANCE: B3 vs NASDAQ'
\echo ''

SELECT
  'B3 (Brasil)' as mercado,
  COUNT(*) as "# Empresas",
  ROUND(AVG(change_pct)::numeric, 2) as "Média %",
  ROUND(MAX(change_pct)::numeric, 2) as "Máx %",
  ROUND(MIN(change_pct)::numeric, 2) as "Mín %"
FROM sofia.market_data_brazil
UNION ALL
SELECT
  'NASDAQ (US)' as mercado,
  COUNT(*) as "# Empresas",
  ROUND(AVG(change_pct)::numeric, 2) as "Média %",
  ROUND(MAX(change_pct)::numeric, 2) as "Máx %",
  ROUND(MIN(change_pct)::numeric, 2) as "Mín %"
FROM sofia.market_data_nasdaq
ORDER BY "Média %" DESC;

\echo ''
\echo '💰 2. FUNDING: Top Setores'
\echo ''

SELECT
  sector as "Setor",
  COUNT(*) as "# Deals",
  SUM(amount_usd) / 1000000000.0 as "Total ($B)",
  ROUND(AVG(amount_usd) / 1000000.0::numeric, 1) as "Média ($M)"
FROM sofia.funding_rounds
GROUP BY sector
ORDER BY "Total ($B)" DESC;

\echo ''
\echo '🎯 3. PARADOXO: Funding vs Performance'
\echo ''

WITH funding_by_sector AS (
  SELECT
    sector,
    SUM(amount_usd) / 1000000000.0 as funding_b
  FROM sofia.funding_rounds
  GROUP BY sector
),
performance_by_sector AS (
  SELECT
    sector,
    ROUND(AVG(change_pct)::numeric, 2) as avg_perf
  FROM sofia.market_data_brazil
  GROUP BY sector
)
SELECT
  COALESCE(f.sector, p.sector) as "Setor",
  COALESCE(f.funding_b, 0) as "Funding ($B)",
  COALESCE(p.avg_perf, 0) as "Performance (%)",
  CASE
    WHEN f.funding_b > 1 AND p.avg_perf = 0 THEN '🔴 Alto funding, 0 performance'
    WHEN f.funding_b = 0 AND p.avg_perf > 2 THEN '🟢 0 funding, alta performance'
    WHEN f.funding_b > 0 AND p.avg_perf > 2 THEN '🟡 Funding + Performance'
    ELSE '⚪ Normal'
  END as "Status"
FROM funding_by_sector f
FULL OUTER JOIN performance_by_sector p ON f.sector = p.sector
ORDER BY "Funding ($B)" DESC, "Performance (%)" DESC;

\echo ''
\echo '🔥 4. TOP PERFORMERS B3 (Hoje)'
\echo ''

SELECT
  ticker as "Ticker",
  company as "Empresa",
  sector as "Setor",
  ROUND(price::numeric, 2) as "Preço (R$)",
  ROUND(change_pct::numeric, 2) as "Variação (%)"
FROM sofia.market_data_brazil
ORDER BY change_pct DESC
LIMIT 10;

\echo ''
\echo '❄️  5. WORST PERFORMERS B3 (Hoje)'
\echo ''

SELECT
  ticker as "Ticker",
  company as "Empresa",
  sector as "Setor",
  ROUND(price::numeric, 2) as "Preço (R$)",
  ROUND(change_pct::numeric, 2) as "Variação (%)"
FROM sofia.market_data_brazil
ORDER BY change_pct ASC
LIMIT 10;

\echo ''
\echo '💸 6. MEGA DEALS (>$500M)'
\echo ''

SELECT
  company_name as "Empresa",
  sector as "Setor",
  round_type as "Round",
  amount_usd / 1000000000.0 as "Valor ($B)",
  announced_date as "Data"
FROM sofia.funding_rounds
WHERE amount_usd > 500000000
ORDER BY amount_usd DESC;

\echo ''
\echo '📊 7. RESUMO GERAL'
\echo ''

SELECT
  'Total de empresas B3' as "Métrica",
  COUNT(*)::text as "Valor"
FROM sofia.market_data_brazil
UNION ALL
SELECT
  'Performance média B3 (%)',
  ROUND(AVG(change_pct)::numeric, 2)::text
FROM sofia.market_data_brazil
UNION ALL
SELECT
  'Total de empresas NASDAQ',
  COUNT(*)::text
FROM sofia.market_data_nasdaq
UNION ALL
SELECT
  'Performance média NASDAQ (%)',
  ROUND(AVG(change_pct)::numeric, 2)::text
FROM sofia.market_data_nasdaq
UNION ALL
SELECT
  'Total de funding rounds',
  COUNT(*)::text
FROM sofia.funding_rounds
UNION ALL
SELECT
  'Capital total investido ($B)',
  ROUND((SUM(amount_usd) / 1000000000.0)::numeric, 2)::text
FROM sofia.funding_rounds;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo '✅ Insights gerados com sucesso!'
\echo ''
\echo '🤖 Para análise com IA: ./generate-insights.sh'
\echo '📊 Para Jupyter Lab: http://91.98.158.19:8889'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
