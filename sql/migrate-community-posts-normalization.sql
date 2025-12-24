-- ============================================================
-- MIGRAÇÃO: Normalizar community_posts
-- Migra author VARCHAR -> author_id FK
-- ============================================================

-- 1. Adicionar coluna author_id
ALTER TABLE sofia.community_posts 
ADD COLUMN IF NOT EXISTS author_id INTEGER REFERENCES sofia.authors(id);

-- 2. Popular authors master table
INSERT INTO sofia.authors (name, normalized_name, platform)
SELECT DISTINCT
    author,
    normalize_string(author),
    source
FROM sofia.community_posts
WHERE author IS NOT NULL
ON CONFLICT (normalized_name, platform) DO NOTHING;

-- 3. Popular author_id
UPDATE sofia.community_posts cp
SET author_id = a.id
FROM sofia.authors a,
     sofia.sources s
WHERE normalize_string(cp.author) = a.normalized_name
  AND cp.source_id = s.id
  AND a.platform = s.name
  AND cp.author_id IS NULL;

-- 4. Criar índice
CREATE INDEX IF NOT EXISTS idx_community_posts_author_id ON sofia.community_posts(author_id);

-- 5. Verificação
SELECT 
    'community_posts normalization' AS status,
    COUNT(*) AS total_records,
    COUNT(author_id) AS with_author_id,
    ROUND(100.0 * COUNT(author_id) / NULLIF(COUNT(*), 0), 2) AS pct_normalized
FROM sofia.community_posts;

SELECT 
    'Unique authors' AS metric,
    COUNT(DISTINCT author_id) AS count
FROM sofia.community_posts
WHERE author_id IS NOT NULL;
