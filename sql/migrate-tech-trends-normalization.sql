-- ============================================================
-- MIGRAÇÃO: Normalizar tech_trends
-- Migra name VARCHAR -> trend_id FK
-- ============================================================

-- 1. Adicionar coluna trend_id
ALTER TABLE sofia.tech_trends 
ADD COLUMN IF NOT EXISTS trend_id INTEGER REFERENCES sofia.trends(id);

-- 2. Popular trends master table com dados existentes
INSERT INTO sofia.trends (name, normalized_name, category)
SELECT DISTINCT
    name,
    normalize_string(name),
    category
FROM sofia.tech_trends
WHERE name IS NOT NULL
ON CONFLICT (normalized_name) DO NOTHING;

-- 3. Popular trend_id na tech_trends
UPDATE sofia.tech_trends tt
SET trend_id = t.id
FROM sofia.trends t
WHERE normalize_string(tt.name) = t.normalized_name
AND tt.trend_id IS NULL;

-- 4. Criar índice
CREATE INDEX IF NOT EXISTS idx_tech_trends_trend_id ON sofia.tech_trends(trend_id);

-- 5. Atualizar constraint UNIQUE
-- Remover constraint antiga se existir
ALTER TABLE sofia.tech_trends DROP CONSTRAINT IF EXISTS tech_trends_source_name_period_start_key;

-- Adicionar nova constraint com trend_id
ALTER TABLE sofia.tech_trends 
ADD CONSTRAINT tech_trends_source_trend_period_unique 
UNIQUE(source_id, trend_id, period_start);

-- 6. Verificação
SELECT 
    'tech_trends normalization' AS status,
    COUNT(*) AS total_records,
    COUNT(trend_id) AS with_trend_id,
    ROUND(100.0 * COUNT(trend_id) / NULLIF(COUNT(*), 0), 2) AS pct_normalized
FROM sofia.tech_trends;

SELECT 
    'Unique trends' AS metric,
    COUNT(DISTINCT trend_id) AS count
FROM sofia.tech_trends
WHERE trend_id IS NOT NULL;
