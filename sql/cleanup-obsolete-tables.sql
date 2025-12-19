-- ============================================================
-- LIMPEZA DE TABELAS OBSOLETAS
-- Remove tabelas que foram consolidadas/substituídas
-- ============================================================

-- ATENÇÃO: Execute apenas após validar que os dados foram migrados!

BEGIN;

-- Tabelas consolidadas em tech_trends
DROP TABLE IF EXISTS sofia.ai_github_trends CASCADE;
DROP TABLE IF EXISTS sofia.stackoverflow_trends CASCADE;
DROP TABLE IF EXISTS sofia.tech_job_skill_trends CASCADE;
DROP TABLE IF EXISTS sofia.tech_job_salary_trends CASCADE;

-- Tabelas consolidadas em community_posts
DROP TABLE IF EXISTS sofia.hacker_news_stories CASCADE;
DROP TABLE IF EXISTS sofia.reddit_tech CASCADE;
DROP TABLE IF EXISTS sofia.reddit_tech_posts CASCADE;

-- Tabelas consolidadas em patents
DROP TABLE IF EXISTS sofia.person_patents CASCADE;

-- Tabelas duplicadas vazias
DROP TABLE IF EXISTS sofia.tech_embedding_jobs CASCADE;

-- Tabelas temporárias não mais usadas
DROP TABLE IF EXISTS sofia.countries_normalization CASCADE;

-- Tabelas de columnists (migradas para persons)
DROP TABLE IF EXISTS sofia.columnist_insights CASCADE;
DROP TABLE IF EXISTS sofia.columnist_papers CASCADE;
DROP TABLE IF EXISTS sofia.columnists CASCADE;

COMMIT;

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================

SELECT 
    'Tabelas restantes' AS info,
    COUNT(*) AS total
FROM information_schema.tables
WHERE table_schema = 'sofia'
AND table_type = 'BASE TABLE';

SELECT 
    table_name
FROM information_schema.tables
WHERE table_schema = 'sofia'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
