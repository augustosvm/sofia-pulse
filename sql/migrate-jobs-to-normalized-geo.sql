-- Migração da tabela sofia.jobs para usar IDs normalizados
-- Fase 3: Adicionar colunas e popular com dados normalizados

-- 1. Adicionar novas colunas
ALTER TABLE sofia.jobs 
ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
ADD COLUMN IF NOT EXISTS state_id INTEGER REFERENCES sofia.states(id),
ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id);

-- 2. Popular country_id usando a função de normalização
UPDATE sofia.jobs
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

-- 3. Popular state_id (para países que temos estados)
UPDATE sofia.jobs
SET state_id = get_or_create_state(state, country_id)
WHERE state IS NOT NULL 
  AND country_id IS NOT NULL 
  AND state_id IS NULL;

-- 4. Popular city_id
UPDATE sofia.jobs
SET city_id = get_or_create_city(city, state_id, country_id)
WHERE city IS NOT NULL 
  AND country_id IS NOT NULL 
  AND city_id IS NULL;

-- 5. Criar índices nas novas colunas
CREATE INDEX IF NOT EXISTS idx_jobs_country_id ON sofia.jobs(country_id);
CREATE INDEX IF NOT EXISTS idx_jobs_state_id ON sofia.jobs(state_id);
CREATE INDEX IF NOT EXISTS idx_jobs_city_id ON sofia.jobs(city_id);

-- 6. Estatísticas da migração
SELECT 
    'Jobs Migration Statistics' AS report,
    COUNT(*) AS total_jobs,
    COUNT(country_id) AS with_country_id,
    COUNT(state_id) AS with_state_id,
    COUNT(city_id) AS with_city_id,
    ROUND(100.0 * COUNT(country_id) / COUNT(*), 2) AS pct_country,
    ROUND(100.0 * COUNT(state_id) / COUNT(*), 2) AS pct_state,
    ROUND(100.0 * COUNT(city_id) / COUNT(*), 2) AS pct_city
FROM sofia.jobs;

-- 7. Verificar países não normalizados
SELECT 
    country,
    COUNT(*) AS count,
    normalize_country_name(country) AS normalized
FROM sofia.jobs
WHERE country IS NOT NULL AND country_id IS NULL
GROUP BY country
ORDER BY count DESC
LIMIT 20;
