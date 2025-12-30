-- ============================================================
-- CONSOLIDAÇÃO: COMMUNITY POSTS
-- Consolida 4 tabelas → 1 tabela unificada
-- ============================================================

-- 1. CRIAR TABELA UNIFICADA
CREATE TABLE IF NOT EXISTS sofia.community_posts (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'hackernews', 'reddit', 'producthunt', 'devto'
    external_id VARCHAR(200),
    
    -- Conteúdo
    title TEXT NOT NULL,
    url TEXT,
    content TEXT,
    author VARCHAR(200),
    
    -- Engagement
    score INTEGER,
    comments_count INTEGER,
    upvotes INTEGER,
    
    -- Classificação
    category VARCHAR(100),
    tags JSONB,
    
    -- Temporal
    posted_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata flexível
    metadata JSONB,
    
    -- Constraints
    UNIQUE(source, external_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_community_posts_source ON sofia.community_posts(source);
CREATE INDEX IF NOT EXISTS idx_community_posts_posted ON sofia.community_posts(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_posts_score ON sofia.community_posts(score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_community_posts_author ON sofia.community_posts(author);
CREATE INDEX IF NOT EXISTS idx_community_posts_collected ON sofia.community_posts(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_posts_tags ON sofia.community_posts USING GIN(tags);

-- 2. MIGRAR DADOS EXISTENTES

-- Migrar hackernews_stories (667 registros)
INSERT INTO sofia.community_posts (
    source, external_id, title, url, content,
    author, score, comments_count,
    posted_at, collected_at, metadata
)
SELECT 
    'hackernews' as source,
    id::TEXT as external_id,
    title,
    url,
    text as content,
    by as author,
    score,
    descendants as comments_count,
    to_timestamp(time) as posted_at,
    collected_at,
    jsonb_build_object(
        'type', type,
        'descendants', descendants,
        'kids', kids
    ) as metadata
FROM sofia.hackernews_stories
ON CONFLICT (source, external_id) DO NOTHING;

-- 3. VERIFICAR MIGRAÇÃO
SELECT 
    'COMMUNITY_POSTS MIGRATION' as status,
    source,
    COUNT(*) as records,
    MIN(posted_at) as earliest,
    MAX(posted_at) as latest,
    AVG(score)::INTEGER as avg_score
FROM sofia.community_posts
GROUP BY source
ORDER BY source;

-- 4. DELETAR TABELAS VAZIAS E DUPLICATAS (SEGURO)
DROP TABLE IF EXISTS sofia.hacker_news_stories CASCADE;  -- duplicata vazia
DROP TABLE IF EXISTS sofia.reddit_tech CASCADE;  -- vazia
DROP TABLE IF EXISTS sofia.reddit_tech_posts CASCADE;  -- vazia

-- 5. RELATÓRIO FINAL
SELECT 
    'Community Posts Consolidation Complete' as status,
    COUNT(*) as total_records,
    COUNT(DISTINCT source) as sources,
    COUNT(DISTINCT author) as unique_authors,
    SUM(score) as total_score
FROM sofia.community_posts;
