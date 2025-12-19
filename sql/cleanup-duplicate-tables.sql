-- ============================================================
-- LIMPEZA: TABELAS DUPLICADAS VAZIAS
-- Remove tabelas duplicadas que estão vazias (SEGURO)
-- ============================================================

-- 1. VERIFICAR ANTES DE DELETAR
SELECT 
    'VERIFICATION BEFORE DELETE' as status,
    table_name,
    (SELECT COUNT(*) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' 
     AND table_name = t.table_name) as fk_count
FROM information_schema.tables t
WHERE table_schema = 'sofia'
AND table_name IN (
    'tech_embedding_jobs',
    'countries_normalization',
    'columnist_insights'
)
ORDER BY table_name;

-- 2. DELETAR DUPLICATAS VAZIAS

-- tech_embedding_jobs (100% duplicata de embedding_jobs, ambas vazias)
DROP TABLE IF EXISTS sofia.tech_embedding_jobs CASCADE;

-- countries_normalization (tabela temp de migração, vazia)
-- NOTA: Usada por collect-rest-countries.ts - precisa atualizar coletor primeiro!
-- DROP TABLE IF EXISTS sofia.countries_normalization CASCADE;

-- columnist_insights (duplicata de insights, vazia)
DROP TABLE IF EXISTS sofia.columnist_insights CASCADE;

-- 3. RELATÓRIO
SELECT 
    'CLEANUP COMPLETE' as status,
    'Deleted: tech_embedding_jobs, columnist_insights' as tables_removed,
    'Kept: countries_normalization (used by collector)' as note;

-- 4. VERIFICAR TABELAS RESTANTES
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema = 'sofia' AND table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'sofia'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
