-- ============================================================================
-- SOFIA PULSE - FINANCE INSIGHTS (Dados Reais)
-- ============================================================================
-- Queries prontas para rodar com os dados coletados hoje!
--
-- Uso:
--   docker exec -it sofia-postgres psql -U sofia -d sofia_db -f finance-insights-now.sql
--
-- Ou copiar/colar queries individuais no psql
-- ============================================================================

\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo '📊 SOFIA PULSE - FINANCE INSIGHTS'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo ''

-- ============================================================================
-- 1. RESUMO GERAL - Quantos dados temos?
-- ============================================================================
\echo '1️⃣  RESUMO GERAL'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

SELECT
  'Brasil (B3)' as mercado,
  COUNT(*) as registros,
  MAX(collected_at)::date as ultima_coleta,
  COUNT(DISTINCT ticker) as ativos_unicos
FROM sofia.market_data_brazil
UNION ALL
SELECT
  'NASDAQ (US)',
  COUNT(*),
  MAX(collected_at)::date,
  COUNT(DISTINCT ticker)
FROM sofia.market_data_nasdaq
UNION ALL
SELECT
  'Funding Rounds',
  COUNT(*),
  MAX(collected_at)::date,
  COUNT(DISTINCT company_name)
FROM sofia.funding_rounds;

\echo ''

-- ============================================================================
-- 2. TOP PERFORMERS - Maiores altas hoje
-- ============================================================================
\echo '2️⃣  TOP PERFORMERS - Maiores Altas'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

\echo ''
\echo '🇧🇷 Brasil (B3):'
SELECT
  ticker,
  company,
  price as "Preço (R$)",
  change_pct as "Variação %",
  volume as "Volume",
  market_cap / 1000000000 as "Market Cap (B)"
FROM sofia.market_data_brazil
WHERE collected_at >= CURRENT_DATE
ORDER BY change_pct DESC
LIMIT 10;

\echo ''
\echo '🇺🇸 NASDAQ:'
SELECT
  ticker,
  company,
  price as "Preço ($)",
  change_pct as "Variação %",
  volume as "Volume",
  market_cap / 1000000000 as "Market Cap (B)"
FROM sofia.market_data_nasdaq
WHERE collected_at >= CURRENT_DATE
ORDER BY change_pct DESC
LIMIT 10;

\echo ''

-- ============================================================================
-- 3. SECTOR ANALYSIS - Desempenho por setor
-- ============================================================================
\echo '3️⃣  ANÁLISE POR SETOR'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

\echo ''
\echo '🇧🇷 Brasil (B3) - Por Setor:'
SELECT
  sector as setor,
  COUNT(*) as num_empresas,
  ROUND(AVG(change_pct), 2) as "Var Média %",
  ROUND(AVG(price), 2) as "Preço Médio",
  SUM(volume) as "Volume Total"
FROM sofia.market_data_brazil
WHERE collected_at >= CURRENT_DATE
GROUP BY sector
ORDER BY "Var Média %" DESC;

\echo ''
\echo '🇺🇸 NASDAQ - Por Setor:'
SELECT
  sector as setor,
  COUNT(*) as num_empresas,
  ROUND(AVG(change_pct), 2) as "Var Média %",
  ROUND(AVG(price), 2) as "Preço Médio",
  SUM(volume) as "Volume Total"
FROM sofia.market_data_nasdaq
WHERE collected_at >= CURRENT_DATE
GROUP BY sector
ORDER BY "Var Média %" DESC;

\echo ''

-- ============================================================================
-- 4. FUNDING INSIGHTS - Onde está indo o dinheiro?
-- ============================================================================
\echo '4️⃣  FUNDING ROUNDS - Onde está o dinheiro?'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

\echo ''
\echo '💰 Top Deals (Maiores Rodadas):'
SELECT
  company_name as empresa,
  sector as setor,
  round_type as rodada,
  amount_usd / 1000000000.0 as "Valor ($B)",
  valuation_usd / 1000000000.0 as "Valuation ($B)",
  announced_date as data
FROM sofia.funding_rounds
WHERE collected_at >= CURRENT_DATE
ORDER BY amount_usd DESC;

\echo ''
\echo '📊 Por Setor (Total Investido):'
SELECT
  sector as setor,
  COUNT(*) as num_deals,
  SUM(amount_usd) / 1000000000.0 as "Total Investido ($B)",
  AVG(amount_usd) / 1000000.0 as "Média por Deal ($M)",
  AVG(valuation_usd) / 1000000000.0 as "Valuation Médio ($B)"
FROM sofia.funding_rounds
WHERE collected_at >= CURRENT_DATE
GROUP BY sector
ORDER BY "Total Investido ($B)" DESC;

\echo ''
\echo '🏆 Por Tipo de Rodada:'
SELECT
  round_type as tipo,
  COUNT(*) as num_deals,
  SUM(amount_usd) / 1000000000.0 as "Total ($B)",
  AVG(amount_usd) / 1000000.0 as "Média ($M)"
FROM sofia.funding_rounds
WHERE collected_at >= CURRENT_DATE
GROUP BY round_type
ORDER BY "Total ($B)" DESC;

\echo ''

-- ============================================================================
-- 5. CORRELATION - Tendências entre mercados
-- ============================================================================
\echo '5️⃣  CORRELAÇÃO - Brasil vs NASDAQ'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

WITH brasil_avg AS (
  SELECT AVG(change_pct) as br_avg
  FROM sofia.market_data_brazil
  WHERE collected_at >= CURRENT_DATE
),
nasdaq_avg AS (
  SELECT AVG(change_pct) as us_avg
  FROM sofia.market_data_nasdaq
  WHERE collected_at >= CURRENT_DATE
)
SELECT
  'Brasil (B3)' as mercado,
  ROUND(br_avg, 2) as "Variação Média %",
  CASE
    WHEN br_avg > 2 THEN '🚀 ALTA FORTE'
    WHEN br_avg > 0 THEN '📈 ALTA'
    WHEN br_avg > -2 THEN '📉 QUEDA LEVE'
    ELSE '📉 QUEDA FORTE'
  END as sentimento
FROM brasil_avg
UNION ALL
SELECT
  'NASDAQ (US)',
  ROUND(us_avg, 2),
  CASE
    WHEN us_avg > 2 THEN '🚀 ALTA FORTE'
    WHEN us_avg > 0 THEN '📈 ALTA'
    WHEN us_avg > -2 THEN '📉 QUEDA LEVE'
    ELSE '📉 QUEDA FORTE'
  END
FROM nasdaq_avg;

\echo ''

-- ============================================================================
-- 6. OPORTUNIDADES - Signals de compra/venda
-- ============================================================================
\echo '6️⃣  OPORTUNIDADES - Signals de Investimento'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

\echo ''
\echo '🇧🇷 Brasil - High Momentum (> 3%):'
SELECT
  ticker,
  company,
  sector,
  change_pct as "Variação %",
  volume,
  CASE
    WHEN change_pct > 5 THEN '🚀 STRONG BUY'
    WHEN change_pct > 3 THEN '✅ BUY'
    ELSE '📊 WATCH'
  END as signal
FROM sofia.market_data_brazil
WHERE collected_at >= CURRENT_DATE
  AND change_pct > 3
ORDER BY change_pct DESC;

\echo ''
\echo '🇺🇸 NASDAQ - High Momentum (> 2%):'
SELECT
  ticker,
  company,
  sector,
  change_pct as "Variação %",
  volume,
  CASE
    WHEN change_pct > 5 THEN '🚀 STRONG BUY'
    WHEN change_pct > 2 THEN '✅ BUY'
    ELSE '📊 WATCH'
  END as signal
FROM sofia.market_data_nasdaq
WHERE collected_at >= CURRENT_DATE
  AND change_pct > 2
ORDER BY change_pct DESC;

\echo ''

-- ============================================================================
-- 7. HOT SECTORS - Setores recebendo mais funding
-- ============================================================================
\echo '7️⃣  HOT SECTORS - Setores Quentes'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

WITH sector_funding AS (
  SELECT
    sector,
    SUM(amount_usd) as total_funding,
    COUNT(*) as num_deals,
    AVG(valuation_usd) as avg_valuation
  FROM sofia.funding_rounds
  WHERE collected_at >= CURRENT_DATE
  GROUP BY sector
)
SELECT
  sector,
  total_funding / 1000000000.0 as "Total Funding ($B)",
  num_deals as "# Deals",
  avg_valuation / 1000000000.0 as "Avg Valuation ($B)",
  CASE
    WHEN total_funding > 5000000000 THEN '🔥 HYPER HOT'
    WHEN total_funding > 1000000000 THEN '🔥 HOT'
    WHEN total_funding > 100000000 THEN '📈 WARM'
    ELSE '📊 NORMAL'
  END as heat_level
FROM sector_funding
ORDER BY total_funding DESC;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo '✅ Análise Completa!'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo ''
