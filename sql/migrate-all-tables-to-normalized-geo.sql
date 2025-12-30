-- Migração CORRIGIDA de todas as tabelas para normalização geográfica
-- Baseado na estrutura real das tabelas

-- ============================================================
-- 1. NIH_GRANTS (52 registros)
-- Colunas: city, country, state
-- ============================================================
ALTER TABLE sofia.nih_grants 
ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
ADD COLUMN IF NOT EXISTS state_id INTEGER REFERENCES sofia.states(id),
ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id);

UPDATE sofia.nih_grants
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

UPDATE sofia.nih_grants
SET state_id = get_or_create_state(state, country_id)
WHERE state IS NOT NULL AND country_id IS NOT NULL AND state_id IS NULL;

UPDATE sofia.nih_grants
SET city_id = get_or_create_city(city, state_id, country_id)
WHERE city IS NOT NULL AND country_id IS NOT NULL AND city_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_nih_grants_country_id ON sofia.nih_grants(country_id);
CREATE INDEX IF NOT EXISTS idx_nih_grants_state_id ON sofia.nih_grants(state_id);
CREATE INDEX IF NOT EXISTS idx_nih_grants_city_id ON sofia.nih_grants(city_id);

-- ============================================================
-- 2. FUNDING_ROUNDS (77 registros)
-- Colunas: city, country
-- ============================================================
ALTER TABLE sofia.funding_rounds 
ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id);

UPDATE sofia.funding_rounds
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

UPDATE sofia.funding_rounds
SET city_id = get_or_create_city(city, NULL, country_id)
WHERE city IS NOT NULL AND country_id IS NOT NULL AND city_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_funding_country_id ON sofia.funding_rounds(country_id);
CREATE INDEX IF NOT EXISTS idx_funding_city_id ON sofia.funding_rounds(city_id);

-- ============================================================
-- 3. TECH_JOBS (3.674 registros)
-- Colunas: city, country, location (já tem city_id e country_id parciais)
-- ============================================================
-- Atualizar country_id para registros que não têm
UPDATE sofia.tech_jobs
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

-- Atualizar city_id para registros que não têm
UPDATE sofia.tech_jobs
SET city_id = get_or_create_city(city, NULL, country_id)
WHERE city IS NOT NULL AND country_id IS NOT NULL AND city_id IS NULL;

-- Garantir que índices existem
CREATE INDEX IF NOT EXISTS idx_tech_jobs_country_id ON sofia.tech_jobs(country_id);
CREATE INDEX IF NOT EXISTS idx_tech_jobs_city_id ON sofia.tech_jobs(city_id);

-- ============================================================
-- RELATÓRIO FINAL
-- ============================================================
SELECT 
    'MIGRATION COMPLETE' AS status,
    'All tables migrated to normalized geographic structure' AS message;

-- Estatísticas detalhadas
SELECT 
    'jobs' AS table_name, 
    COUNT(*) AS total, 
    COUNT(country_id) AS with_country,
    COUNT(state_id) AS with_state,
    COUNT(city_id) AS with_city,
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2) AS pct_country,
    ROUND(100.0 * COUNT(state_id) / NULLIF(COUNT(*), 0), 2) AS pct_state,
    ROUND(100.0 * COUNT(city_id) / NULLIF(COUNT(*), 0), 2) AS pct_city
FROM sofia.jobs
UNION ALL
SELECT 
    'nih_grants', 
    COUNT(*), 
    COUNT(country_id), 
    COUNT(state_id), 
    COUNT(city_id),
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2),
    ROUND(100.0 * COUNT(state_id) / NULLIF(COUNT(*), 0), 2),
    ROUND(100.0 * COUNT(city_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.nih_grants
UNION ALL
SELECT 
    'funding_rounds', 
    COUNT(*), 
    COUNT(country_id), 
    0, 
    COUNT(city_id),
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2),
    0,
    ROUND(100.0 * COUNT(city_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.funding_rounds
UNION ALL
SELECT 
    'tech_jobs', 
    COUNT(*), 
    COUNT(country_id), 
    0, 
    COUNT(city_id),
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2),
    0,
    ROUND(100.0 * COUNT(city_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.tech_jobs
ORDER BY total DESC;

-- Verificar países/cidades criados
SELECT 
    'Total Countries' AS metric,
    COUNT(*)::TEXT AS value
FROM sofia.countries
UNION ALL
SELECT 
    'Total States',
    COUNT(*)::TEXT
FROM sofia.states
UNION ALL
SELECT 
    'Total Cities',
    COUNT(*)::TEXT
FROM sofia.cities;
