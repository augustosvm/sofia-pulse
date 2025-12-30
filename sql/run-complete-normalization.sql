-- ============================================================
-- MASTER SCRIPT - Normalização Completa do Banco
-- Executa TODAS as normalizações em ordem correta
-- ============================================================

\echo '============================================================'
\echo 'SOFIA PULSE - NORMALIZAÇÃO COMPLETA DO BANCO'
\echo '============================================================'
\echo ''

-- ============================================================
-- FASE 1: TABELAS MASTER (Entidades)
-- ============================================================

\echo '📦 FASE 1: Criando Tabelas Master...'
\echo ''

\echo '1.1 Criando tabela sources...'
\i sql/create-sources-table.sql
\echo ''

\echo '1.2 Criando tabela types...'
\i sql/create-types-table.sql
\echo ''

\echo '1.3 Criando tabelas master (trends, organizations, persons, categories)...'
\i sql/create-master-tables.sql
\echo ''

-- ============================================================
-- FASE 2: EXPANDIR TABELAS EXISTENTES
-- ============================================================

\echo '📦 FASE 2: Expandindo Tabelas Existentes...'
\echo ''

\echo '2.1 Expandindo tabela persons (130k registros)...'
\i sql/expand-persons-table.sql
\echo ''

\echo '2.2 Criando tabela organizations (pessoa jurídica)...'
\i sql/create-organizations-table.sql
\echo ''

-- ============================================================
-- FASE 3: NORMALIZAR DADOS (VARCHARs → FKs)
-- ============================================================

\echo '📦 FASE 3: Normalizando Dados...'
\echo ''

\echo '3.1 Normalizando tech_trends (name → trend_id)...'
\i sql/migrate-tech-trends-normalization.sql
\echo ''

\echo '3.2 Normalizando community_posts (author → person_id)...'
\i sql/migrate-community-posts-normalization.sql
\echo ''

\echo '3.3 Normalizando patents (applicant → organization_id)...'
\i sql/migrate-patents-normalization.sql
\echo ''

-- ============================================================
-- FASE 4: CONSOLIDAR TABELAS DUPLICADAS
-- ============================================================

\echo '📦 FASE 4: Consolidando Tabelas Duplicadas...'
\echo ''

\echo '4.1 Consolidando tech_trends...'
\i sql/consolidate-tech-trends.sql
\echo ''

\echo '4.2 Consolidando community_posts...'
\i sql/consolidate-community-posts.sql
\echo ''

\echo '4.3 Consolidando patents...'
\i sql/consolidate-patents.sql
\echo ''

\echo '4.4 Limpando tabelas duplicadas vazias...'
\i sql/cleanup-duplicate-tables.sql
\echo ''

-- ============================================================
-- RELATÓRIO FINAL
-- ============================================================

\echo '============================================================'
\echo 'RELATÓRIO FINAL - NORMALIZAÇÃO COMPLETA'
\echo '============================================================'
\echo ''

\echo '📊 TABELAS MASTER:'
\echo ''

SELECT 
    'Master Tables' AS category,
    'sources' AS table_name,
    COUNT(*) AS records,
    COUNT(CASE WHEN active THEN 1 END) AS active
FROM sofia.sources
UNION ALL
SELECT 'Master Tables', 'types', COUNT(*), COUNT(CASE WHEN active THEN 1 END)
FROM sofia.types
UNION ALL
SELECT 'Master Tables', 'trends', COUNT(*), COUNT(*)
FROM sofia.trends
UNION ALL
SELECT 'Master Tables', 'organizations', COUNT(*), COUNT(CASE WHEN active THEN 1 END)
FROM sofia.organizations
UNION ALL
SELECT 'Master Tables', 'persons', COUNT(*), COUNT(CASE WHEN active THEN 1 END)
FROM sofia.persons
UNION ALL
SELECT 'Master Tables', 'categories', COUNT(*), COUNT(*)
FROM sofia.categories
UNION ALL
SELECT 'Geographic', 'countries', COUNT(*), COUNT(*)
FROM sofia.countries
UNION ALL
SELECT 'Geographic', 'states', COUNT(*), COUNT(*)
FROM sofia.states
UNION ALL
SELECT 'Geographic', 'cities', COUNT(*), COUNT(*)
FROM sofia.cities
ORDER BY category, table_name;

\echo ''
\echo '📊 COBERTURA DE NORMALIZAÇÃO:'
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
    COUNT(person_id),
    ROUND(100.0 * COUNT(person_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.community_posts
UNION ALL
SELECT 
    'patents',
    COUNT(*),
    COUNT(organization_id),
    ROUND(100.0 * COUNT(organization_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.patents
UNION ALL
SELECT 
    'organizations',
    COUNT(*),
    COUNT(type_id),
    ROUND(100.0 * COUNT(type_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.organizations
UNION ALL
SELECT 
    'persons',
    COUNT(*),
    COUNT(source_id),
    ROUND(100.0 * COUNT(source_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.persons;

\echo ''
\echo '📊 TIPOS POR CATEGORIA:'
\echo ''

SELECT 
    category,
    COUNT(*) AS types_count
FROM sofia.types
WHERE active = true
GROUP BY category
ORDER BY category;

\echo ''
\echo '📊 ORGANIZAÇÕES POR TIPO:'
\echo ''

SELECT 
    t.name AS type,
    COUNT(o.id) AS count
FROM sofia.organizations o
JOIN sofia.types t ON o.type_id = t.id
GROUP BY t.name
ORDER BY count DESC
LIMIT 10;

\echo ''
\echo '📊 PESSOAS POR ROLE:'
\echo ''

SELECT 
    unnest(roles) AS role,
    COUNT(*) AS count
FROM sofia.persons
WHERE roles IS NOT NULL
GROUP BY role
ORDER BY count DESC;

\echo ''
\echo '============================================================'
\echo '✅ NORMALIZAÇÃO COMPLETA EXECUTADA COM SUCESSO!'
\echo '============================================================'
\echo ''
\echo 'PRÓXIMOS PASSOS:'
\echo '1. Atualizar coletores para usar tabelas normalizadas'
\echo '2. Atualizar analytics para usar FKs em vez de VARCHARs'
\echo '3. Remover colunas VARCHAR antigas (após validação)'
\echo '4. Criar views de compatibilidade se necessário'
\echo ''
