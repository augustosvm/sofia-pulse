-- ============================================================================
-- CLEANUP SCRIPT: REMOÇÃO DE TABELAS OBSOLETAS
-- ============================================================================
-- Este script remove as tabelas que foram consolidadas em:
-- 1. sofia.trends
-- 2. sofia.organizations (ex-institutions)
-- 3. sofia.person_roles
-- ============================================================================

-- 1. Remover tabelas de Trends antigas (dados já em sofia.trends)
DROP TABLE IF EXISTS sofia.ai_github_trends CASCADE;
DROP TABLE IF EXISTS sofia.stackoverflow_trends CASCADE;
DROP TABLE IF EXISTS sofia.github_trending CASCADE;
DROP TABLE IF EXISTS sofia.ai_npm_packages CASCADE;
DROP TABLE IF EXISTS sofia.ai_pypi_packages CASCADE;
DROP TABLE IF EXISTS sofia.tech_job_skill_trends CASCADE;
DROP TABLE IF EXISTS sofia.tech_radar CASCADE;

-- 2. Remover tabelas de Instituições antigas (dados já em sofia.organizations)
DROP TABLE IF EXISTS sofia.institutions CASCADE;
DROP TABLE IF EXISTS sofia.brazil_research_institutions CASCADE;
DROP TABLE IF EXISTS sofia.global_research_institutions CASCADE;

-- 3. Remover tabelas vazias ou inúteis de Colunistas (dados já em sofia.persons)
DROP TABLE IF EXISTS sofia.columnists CASCADE; -- Já migrado para persons com role 'columnist'
DROP TABLE IF EXISTS sofia.columnist_insights CASCADE;
DROP TABLE IF EXISTS sofia.columnist_papers CASCADE;

-- 4. Remover outras tabelas temporárias ou obsoletas identificadas
DROP TABLE IF EXISTS sofia.temp_normalized_persons CASCADE;

-- ============================================================================
-- FIM DA LIMPEZA
-- ============================================================================
