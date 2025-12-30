-- ============================================================
-- NORMALIZAÇÃO: SOURCES
-- Cria tabela master de fontes e normaliza foreign keys
-- ============================================================

-- 1. CRIAR TABELA DE FONTES
CREATE TABLE IF NOT EXISTS sofia.sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'tech_trends', 'community', 'patents', etc
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Popular fontes conhecidas
INSERT INTO sofia.sources (name, category, description) VALUES
-- Tech Trends
('github', 'tech_trends', 'GitHub repositories and trends'),
('stackoverflow', 'tech_trends', 'StackOverflow questions and tags'),
('npm', 'tech_trends', 'NPM package downloads and trends'),
('pypi', 'tech_trends', 'PyPI package downloads and trends'),
('crates', 'tech_trends', 'Rust crates.io packages'),
('rubygems', 'tech_trends', 'Ruby gems trends'),

-- Community Posts
('hackernews', 'community', 'Hacker News stories and discussions'),
('reddit', 'community', 'Reddit tech subreddits'),
('producthunt', 'community', 'Product Hunt launches'),
('devto', 'community', 'Dev.to articles'),

-- Patents
('epo', 'patents', 'European Patent Office'),
('wipo', 'patents', 'World Intellectual Property Organization'),
('uspto', 'patents', 'United States Patent and Trademark Office')
ON CONFLICT (name) DO NOTHING;

-- Índices
CREATE INDEX IF NOT EXISTS idx_sources_category ON sofia.sources(category);
CREATE INDEX IF NOT EXISTS idx_sources_active ON sofia.sources(active);

-- ============================================================
-- 2. ATUALIZAR TABELAS CONSOLIDADAS
-- ============================================================

-- Adicionar source_id às tabelas (se ainda não existir)
ALTER TABLE sofia.tech_trends 
ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sofia.sources(id);

ALTER TABLE sofia.community_posts 
ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sofia.sources(id);

ALTER TABLE sofia.patents 
ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sofia.sources(id);

-- Popular source_id baseado no source VARCHAR (se existir dados)
UPDATE sofia.tech_trends t
SET source_id = s.id
FROM sofia.sources s
WHERE t.source = s.name
AND t.source_id IS NULL;

UPDATE sofia.community_posts cp
SET source_id = s.id
FROM sofia.sources s
WHERE cp.source = s.name
AND cp.source_id IS NULL;

UPDATE sofia.patents p
SET source_id = s.id
FROM sofia.sources s
WHERE p.source = s.name
AND p.source_id IS NULL;

-- Criar índices em source_id
CREATE INDEX IF NOT EXISTS idx_tech_trends_source_id ON sofia.tech_trends(source_id);
CREATE INDEX IF NOT EXISTS idx_community_posts_source_id ON sofia.community_posts(source_id);
CREATE INDEX IF NOT EXISTS idx_patents_source_id ON sofia.patents(source_id);

-- ============================================================
-- 3. VERIFICAÇÃO
-- ============================================================

SELECT 
    'SOURCES NORMALIZATION' as status,
    COUNT(*) as total_sources,
    COUNT(CASE WHEN active THEN 1 END) as active_sources
FROM sofia.sources;

SELECT 
    'Sources by Category' as report,
    category,
    COUNT(*) as count
FROM sofia.sources
GROUP BY category;
