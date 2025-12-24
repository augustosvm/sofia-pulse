-- ============================================================
-- MASTER SCRIPT: Normalização Completa
-- Executa todas as normalizações em ordem
-- ============================================================

\echo '============================================================'
\echo 'NORMALIZAÇÃO COMPLETA - Master Tables + Migrations'
\echo '============================================================'
\echo ''

-- 1. Criar tabelas master
\echo '1. Criando tabelas master (trends, companies, authors, categories)...'
\i create-master-tables.sql
\echo ''

-- 2. Normalizar tech_trends
\echo '2. Normalizando tech_trends (name -> trend_id)...'
\i migrate-tech-trends-normalization.sql
\echo ''

-- 3. Normalizar community_posts
\echo '3. Normalizando community_posts (author -> author_id)...'
\i migrate-community-posts-normalization.sql
\echo ''

-- 4. Normalizar patents
\echo '4. Normalizando patents (applicant -> company_id)...'
\i migrate-patents-normalization.sql
\echo ''

-- 5. Relatório final
\echo '============================================================'
\echo 'RELATÓRIO FINAL DE NORMALIZAÇÃO'
\echo '============================================================'
\echo ''

SELECT 
    'Master Tables' AS category,
    'trends' AS table_name,
    COUNT(*) AS records
FROM sofia.trends
UNION ALL
SELECT 'Master Tables', 'companies', COUNT(*) FROM sofia.companies
UNION ALL
SELECT 'Master Tables', 'authors', COUNT(*) FROM sofia.authors
UNION ALL
SELECT 'Master Tables', 'categories', COUNT(*) FROM sofia.categories
UNION ALL
SELECT 'Master Tables', 'sources', COUNT(*) FROM sofia.sources
UNION ALL
SELECT 'Master Tables', 'countries', COUNT(*) FROM sofia.countries
UNION ALL
SELECT 'Master Tables', 'states', COUNT(*) FROM sofia.states
UNION ALL
SELECT 'Master Tables', 'cities', COUNT(*) FROM sofia.cities
ORDER BY category, table_name;

\echo ''
\echo 'Normalization Coverage:'
\echo ''

SELECT 
    'tech_trends' AS table_name,
    COUNT(*) AS total,
    COUNT(trend_id) AS normalized,
    ROUND(100.0 * COUNT(trend_id) / NULLIF(COUNT(*), 0), 2) || '%' AS coverage
FROM sofia.tech_trends
UNION ALL
SELECT 
    'community_posts',
    COUNT(*),
    COUNT(author_id),
    ROUND(100.0 * COUNT(author_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.community_posts
UNION ALL
SELECT 
    'patents',
    COUNT(*),
    COUNT(company_id),
    ROUND(100.0 * COUNT(company_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.patents;

\echo ''
\echo '============================================================'
\echo '✅ NORMALIZAÇÃO COMPLETA!'
\echo '============================================================'
