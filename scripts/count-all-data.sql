-- ============================================================================
-- CONTAGEM EXATA DE DADOS - Todas as tabelas
-- ============================================================================
-- Execute: docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/count-all-data.sql
-- ============================================================================

\echo '============================================================================'
\echo 'CONTAGEM EXATA DE REGISTROS POR TABELA'
\echo '============================================================================'
\echo ''

-- Usar DO block para contar dinamicamente todas as tabelas
DO $$
DECLARE
  r RECORD;
  cnt BIGINT;
  total BIGINT := 0;
BEGIN
  RAISE NOTICE 'Schema | Tabela | Registros';
  RAISE NOTICE '------------------------------------------------------------';

  FOR r IN
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY schemaname, tablename
  LOOP
    EXECUTE format('SELECT COUNT(*) FROM %I.%I', r.schemaname, r.tablename) INTO cnt;
    RAISE NOTICE '% | % | %', r.schemaname, r.tablename, cnt;
    total := total + cnt;
  END LOOP;

  RAISE NOTICE '------------------------------------------------------------';
  RAISE NOTICE 'TOTAL GERAL: % registros', total;
END $$;

\echo ''
\echo '============================================================================'
\echo 'VERIFICANDO DATAS DE COLETA (últimas e primeiras)'
\echo '============================================================================'
\echo ''

-- Cardboard Production
\echo '📦 Cardboard Production:'
SELECT
  COUNT(*) as registros,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta
FROM sofia.cardboard_production;

-- ArXiv AI Papers
\echo ''
\echo '📄 ArXiv AI Papers:'
SELECT
  COUNT(*) as registros,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta
FROM sofia.arxiv_ai_papers;

-- AI Companies
\echo ''
\echo '🏢 AI Companies:'
SELECT
  COUNT(*) as registros,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta
FROM sofia.ai_companies;

-- WIPO China Patents
\echo ''
\echo '🇨🇳 WIPO China Patents:'
SELECT
  COUNT(*) as registros,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta
FROM sofia.wipo_china_patents;

-- HKEX IPOs
\echo ''
\echo '🇭🇰 HKEX IPOs:'
SELECT
  COUNT(*) as registros,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta
FROM sofia.hkex_ipos;

\echo ''
\echo '============================================================================'
\echo 'ANÁLISE COMPLETA'
\echo '============================================================================'
