-- Limpeza COMPLETA e recriação da normalização geográfica
-- Solução: Remover constraints, limpar, recriar

-- 1. REMOVER foreign keys temporariamente
ALTER TABLE sofia.jobs DROP CONSTRAINT IF EXISTS jobs_country_id_fkey;
ALTER TABLE sofia.jobs DROP CONSTRAINT IF EXISTS jobs_state_id_fkey;
ALTER TABLE sofia.jobs DROP CONSTRAINT IF EXISTS jobs_city_id_fkey;

ALTER TABLE sofia.nih_grants DROP CONSTRAINT IF EXISTS nih_grants_country_id_fkey;
ALTER TABLE sofia.nih_grants DROP CONSTRAINT IF EXISTS nih_grants_state_id_fkey;
ALTER TABLE sofia.nih_grants DROP CONSTRAINT IF EXISTS nih_grants_city_id_fkey;

ALTER TABLE sofia.funding_rounds DROP CONSTRAINT IF EXISTS funding_rounds_country_id_fkey;
ALTER TABLE sofia.funding_rounds DROP CONSTRAINT IF EXISTS funding_rounds_city_id_fkey;

ALTER TABLE sofia.tech_jobs DROP CONSTRAINT IF EXISTS tech_jobs_country_id_fkey;
ALTER TABLE sofia.tech_jobs DROP CONSTRAINT IF EXISTS tech_jobs_city_id_fkey;

ALTER TABLE sofia.states DROP CONSTRAINT IF EXISTS states_country_id_fkey;
ALTER TABLE sofia.cities DROP CONSTRAINT IF EXISTS cities_country_id_fkey;
ALTER TABLE sofia.cities DROP CONSTRAINT IF EXISTS cities_state_id_fkey;

-- 2. LIMPAR TUDO
TRUNCATE TABLE sofia.cities CASCADE;
TRUNCATE TABLE sofia.states CASCADE;
DELETE FROM sofia.countries WHERE iso_alpha2 IS NULL;

-- 3. SETAR country_id = NULL em todas as tabelas
UPDATE sofia.jobs SET country_id = NULL, state_id = NULL, city_id = NULL;
UPDATE sofia.nih_grants SET country_id = NULL, state_id = NULL, city_id = NULL;
UPDATE sofia.funding_rounds SET country_id = NULL, city_id = NULL;
UPDATE sofia.tech_jobs SET country_id = NULL, city_id = NULL;

-- 4. MELHORAR função get_or_create_country
CREATE OR REPLACE FUNCTION get_or_create_country(input_name TEXT)
RETURNS INTEGER AS $$
DECLARE
    country_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF input_name IS NULL OR TRIM(input_name) = '' OR LENGTH(TRIM(input_name)) < 2 THEN
        RETURN NULL;
    END IF;
    
    -- Ignorar valores que claramente não são países
    IF LOWER(TRIM(input_name)) IN ('remote', 'worldwide', 'global', 'international', 'n/a', 'none', 'unknown', 'various') THEN
        RETURN NULL;
    END IF;
    
    -- Normalizar nome
    normalized := normalize_country_name(input_name);
    
    -- Buscar ID apenas em países com ISO code
    SELECT id INTO country_id_result
    FROM sofia.countries
    WHERE common_name = normalized
      AND iso_alpha2 IS NOT NULL
    LIMIT 1;
    
    -- Tentar match por ISO code
    IF country_id_result IS NULL THEN
        SELECT id INTO country_id_result
        FROM sofia.countries
        WHERE UPPER(iso_alpha2) = UPPER(TRIM(input_name))
           OR UPPER(iso_alpha3) = UPPER(TRIM(input_name))
        LIMIT 1;
    END IF;
    
    RETURN country_id_result;
END;
$$ LANGUAGE plpgsql;

-- 5. REMIGRAR com função corrigida
UPDATE sofia.jobs
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL;

UPDATE sofia.nih_grants
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL;

UPDATE sofia.funding_rounds
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL;

UPDATE sofia.tech_jobs
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL;

-- 6. RECRIAR foreign keys
ALTER TABLE sofia.states ADD CONSTRAINT states_country_id_fkey 
    FOREIGN KEY (country_id) REFERENCES sofia.countries(id) ON DELETE CASCADE;

ALTER TABLE sofia.cities ADD CONSTRAINT cities_country_id_fkey 
    FOREIGN KEY (country_id) REFERENCES sofia.countries(id) ON DELETE CASCADE;
    
ALTER TABLE sofia.cities ADD CONSTRAINT cities_state_id_fkey 
    FOREIGN KEY (state_id) REFERENCES sofia.states(id) ON DELETE SET NULL;

ALTER TABLE sofia.jobs ADD CONSTRAINT jobs_country_id_fkey 
    FOREIGN KEY (country_id) REFERENCES sofia.countries(id);
    
ALTER TABLE sofia.jobs ADD CONSTRAINT jobs_state_id_fkey 
    FOREIGN KEY (state_id) REFERENCES sofia.states(id);
    
ALTER TABLE sofia.jobs ADD CONSTRAINT jobs_city_id_fkey 
    FOREIGN KEY (city_id) REFERENCES sofia.cities(id);

-- 7. RELATÓRIO FINAL
SELECT 'CLEANUP COMPLETE' AS status;

SELECT 
    'Total Countries' AS metric,
    COUNT(*)::TEXT AS value
FROM sofia.countries
UNION ALL
SELECT 'Total States', COUNT(*)::TEXT FROM sofia.states
UNION ALL
SELECT 'Total Cities', COUNT(*)::TEXT FROM sofia.cities;

SELECT 
    'jobs' AS table_name, 
    COUNT(*) AS total, 
    COUNT(country_id) AS with_country,
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2) AS pct
FROM sofia.jobs
UNION ALL
SELECT 'nih_grants', COUNT(*), COUNT(country_id), ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.nih_grants
UNION ALL
SELECT 'funding_rounds', COUNT(*), COUNT(country_id), ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.funding_rounds
UNION ALL
SELECT 'tech_jobs', COUNT(*), COUNT(country_id), ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.tech_jobs
ORDER BY total DESC;
