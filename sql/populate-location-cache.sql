-- Sistema de Cache de Localizações
-- Popula cidades/estados com dados já existentes nas tabelas
-- Evita usar Google Maps para localizações já conhecidas

-- 1. Popular estados a partir de dados existentes
INSERT INTO sofia.states (name, country_id)
SELECT DISTINCT 
    TRIM(state) as name,
    country_id
FROM sofia.jobs
WHERE state IS NOT NULL 
  AND TRIM(state) != ''
  AND country_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM sofia.states s 
      WHERE LOWER(s.name) = LOWER(TRIM(jobs.state)) 
      AND s.country_id = jobs.country_id
  )
ON CONFLICT (name, country_id) DO NOTHING;

-- Adicionar estados de outras tabelas
INSERT INTO sofia.states (name, country_id)
SELECT DISTINCT 
    TRIM(state) as name,
    country_id
FROM sofia.nih_grants
WHERE state IS NOT NULL 
  AND TRIM(state) != ''
  AND country_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM sofia.states s 
      WHERE LOWER(s.name) = LOWER(TRIM(nih_grants.state)) 
      AND s.country_id = nih_grants.country_id
  )
ON CONFLICT (name, country_id) DO NOTHING;

-- 2. Popular cidades a partir de dados existentes
INSERT INTO sofia.cities (name, state_id, country_id)
SELECT DISTINCT 
    TRIM(j.city) as name,
    s.id as state_id,
    j.country_id
FROM sofia.jobs j
LEFT JOIN sofia.states s ON LOWER(s.name) = LOWER(TRIM(j.state)) AND s.country_id = j.country_id
WHERE j.city IS NOT NULL 
  AND TRIM(j.city) != ''
  AND j.country_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM sofia.cities c 
      WHERE LOWER(c.name) = LOWER(TRIM(j.city)) 
      AND (c.state_id = s.id OR (c.state_id IS NULL AND s.id IS NULL))
      AND c.country_id = j.country_id
  )
ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- Adicionar cidades de outras tabelas
INSERT INTO sofia.cities (name, country_id)
SELECT DISTINCT 
    TRIM(city) as name,
    country_id
FROM sofia.nih_grants
WHERE city IS NOT NULL 
  AND TRIM(city) != ''
  AND country_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM sofia.cities c 
      WHERE LOWER(c.name) = LOWER(TRIM(nih_grants.city)) 
      AND c.country_id = nih_grants.country_id
  )
ON CONFLICT (name, state_id, country_id) DO NOTHING;

INSERT INTO sofia.cities (name, country_id)
SELECT DISTINCT 
    TRIM(city) as name,
    country_id
FROM sofia.funding_rounds
WHERE city IS NOT NULL 
  AND TRIM(city) != ''
  AND country_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM sofia.cities c 
      WHERE LOWER(c.name) = LOWER(TRIM(funding_rounds.city)) 
      AND c.country_id = funding_rounds.country_id
  )
ON CONFLICT (name, state_id, country_id) DO NOTHING;

INSERT INTO sofia.cities (name, country_id)
SELECT DISTINCT 
    TRIM(city) as name,
    country_id
FROM sofia.tech_jobs
WHERE city IS NOT NULL 
  AND TRIM(city) != ''
  AND country_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM sofia.cities c 
      WHERE LOWER(c.name) = LOWER(TRIM(tech_jobs.city)) 
      AND c.country_id = tech_jobs.country_id
  )
ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- 3. Atualizar state_id e city_id nas tabelas usando o cache
UPDATE sofia.jobs j
SET state_id = s.id
FROM sofia.states s
WHERE LOWER(s.name) = LOWER(TRIM(j.state))
  AND s.country_id = j.country_id
  AND j.state_id IS NULL
  AND j.state IS NOT NULL;

UPDATE sofia.jobs j
SET city_id = c.id
FROM sofia.cities c
LEFT JOIN sofia.states s ON c.state_id = s.id
WHERE LOWER(c.name) = LOWER(TRIM(j.city))
  AND c.country_id = j.country_id
  AND (c.state_id = j.state_id OR (c.state_id IS NULL AND j.state_id IS NULL))
  AND j.city_id IS NULL
  AND j.city IS NOT NULL;

UPDATE sofia.nih_grants ng
SET state_id = s.id
FROM sofia.states s
WHERE LOWER(s.name) = LOWER(TRIM(ng.state))
  AND s.country_id = ng.country_id
  AND ng.state_id IS NULL
  AND ng.state IS NOT NULL;

UPDATE sofia.nih_grants ng
SET city_id = c.id
FROM sofia.cities c
WHERE LOWER(c.name) = LOWER(TRIM(ng.city))
  AND c.country_id = ng.country_id
  AND ng.city_id IS NULL
  AND ng.city IS NOT NULL;

UPDATE sofia.funding_rounds fr
SET city_id = c.id
FROM sofia.cities c
WHERE LOWER(c.name) = LOWER(TRIM(fr.city))
  AND c.country_id = fr.country_id
  AND fr.city_id IS NULL
  AND fr.city IS NOT NULL;

UPDATE sofia.tech_jobs tj
SET city_id = c.id
FROM sofia.cities c
WHERE LOWER(c.name) = LOWER(TRIM(tj.city))
  AND c.country_id = tj.country_id
  AND tj.city_id IS NULL
  AND tj.city IS NOT NULL;

-- 4. RELATÓRIO FINAL
SELECT 'LOCATION CACHE POPULATED' AS status;

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
    COUNT(state_id) AS with_state,
    COUNT(city_id) AS with_city,
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2) AS pct_country,
    ROUND(100.0 * COUNT(state_id) / NULLIF(COUNT(*), 0), 2) AS pct_state,
    ROUND(100.0 * COUNT(city_id) / NULLIF(COUNT(*), 0), 2) AS pct_city
FROM sofia.jobs
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
ORDER BY total DESC;

-- Localizações que ainda precisariam do Google Maps (amostra)
SELECT 
    'Localizações sem normalização (precisariam Google Maps):' AS info,
    COUNT(*) AS count
FROM sofia.jobs
WHERE country_id IS NULL AND (country IS NOT NULL OR city IS NOT NULL OR state IS NOT NULL);
