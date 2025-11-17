-- ============================================================================
-- INVESTIGAÇÃO COMPLETA DO BANCO DE DADOS
-- ============================================================================
-- Execute este arquivo no psql:
-- docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql
-- ============================================================================

\echo '========================================='
\echo '1. INFORMAÇÕES BÁSICAS'
\echo '========================================='
SELECT version();
SELECT current_database() as database, current_user as user, inet_server_addr() as host;

\echo ''
\echo '========================================='
\echo '2. TODOS OS SCHEMAS'
\echo '========================================='
\dn+

\echo ''
\echo '========================================='
\echo '3. SEARCH PATH ATUAL'
\echo '========================================='
SHOW search_path;

\echo ''
\echo '========================================='
\echo '4. TODAS AS TABELAS (TODOS OS SCHEMAS)'
\echo '========================================='
SELECT
  schemaname,
  tablename,
  tableowner
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;

\echo ''
\echo '========================================='
\echo '5. CONTAGEM DE REGISTROS POR TABELA'
\echo '========================================='
SELECT
  schemaname,
  tablename,
  n_live_tup as registros_aproximados
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

\echo ''
\echo '========================================='
\echo '6. ESTATÍSTICAS PRECISAS (pode demorar)'
\echo '========================================='
-- Esta query conta EXATAMENTE quantos registros existem

DO $$
DECLARE
  r RECORD;
  cnt BIGINT;
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE 'Tabela | Registros Exatos';
  RAISE NOTICE '----------------------------------------';

  FOR r IN
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY tablename
  LOOP
    EXECUTE format('SELECT COUNT(*) FROM %I.%I', r.schemaname, r.tablename) INTO cnt;
    RAISE NOTICE '% | %', r.tablename, cnt;
  END LOOP;
END $$;

\echo ''
\echo '========================================='
\echo '7. LISTA DE DATABASES DISPONÍVEIS'
\echo '========================================='
\l

\echo ''
\echo '========================================='
\echo 'INVESTIGAÇÃO CONCLUÍDA'
\echo '========================================='
