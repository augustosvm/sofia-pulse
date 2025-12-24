-- ============================================================
-- MASTER SCRIPT: CONSOLIDAÇÃO COMPLETA
-- Executa todas as consolidações em ordem
-- ============================================================

\echo '============================================================'
\echo 'INICIANDO CONSOLIDAÇÃO DE TABELAS'
\echo '============================================================'
\echo ''

-- 1. LIMPEZA DE DUPLICATAS VAZIAS
\echo '1. Limpando tabelas duplicadas vazias...'
\i cleanup-duplicate-tables.sql
\echo ''

-- 2. CONSOLIDAR TECH TRENDS
\echo '2. Consolidando Tech Trends...'
\i consolidate-tech-trends.sql
\echo ''

-- 3. CONSOLIDAR COMMUNITY POSTS
\echo '3. Consolidando Community Posts...'
\i consolidate-community-posts.sql
\echo ''

-- 4. CONSOLIDAR PATENTS
\echo '4. Consolidando Patents...'
\i consolidate-patents.sql
\echo ''

-- 5. RELATÓRIO FINAL CONSOLIDADO
\echo '============================================================'
\echo 'RELATÓRIO FINAL DE CONSOLIDAÇÃO'
\echo '============================================================'
\echo ''

SELECT 
    'SUMMARY' as report,
    'Tables Before' as metric,
    '154' as value
UNION ALL
SELECT 'SUMMARY', 'Tables After', (
    SELECT COUNT(*)::TEXT 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia' AND table_type = 'BASE TABLE'
)
UNION ALL
SELECT 'SUMMARY', 'Tables Removed', (154 - (
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia' AND table_type = 'BASE TABLE'
))::TEXT
UNION ALL
SELECT 'SUMMARY', 'Tables Created', '3';

\echo ''
\echo 'Detalhes das novas tabelas:'
\echo ''

SELECT 
    'tech_trends' as table_name,
    COUNT(*) as records,
    COUNT(DISTINCT source) as sources
FROM sofia.tech_trends
UNION ALL
SELECT 
    'community_posts',
    COUNT(*),
    COUNT(DISTINCT source)
FROM sofia.community_posts
UNION ALL
SELECT 
    'patents',
    COUNT(*),
    COUNT(DISTINCT source)
FROM sofia.patents;

\echo ''
\echo '============================================================'
\echo '✅ CONSOLIDAÇÃO COMPLETA!'
\echo '============================================================'
