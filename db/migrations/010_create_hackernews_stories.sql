-- ============================================================================
-- Migration: HackerNews Stories Table
-- ============================================================================
-- Collector: collect-hackernews.ts
-- Fonte: HackerNews Algolia API (https://hn.algolia.com/api/v1)
-- Frequência: Diário, 08:30 UTC
--
-- Objetivo: Capturar BUZZ tecnológico ANTES de virar mainstream
--           HN = termômetro de interesse da comunidade tech
--
-- WEAK SIGNALS:
-- - Stories com 100+ points em <24h: Tema esquentando
-- - Comments > 50: Debate ativo (polarização ou interesse real)
-- - Autor conhecido (patio11, antirez, etc): Credibilidade alta
-- - Timing: Story sobre tecnologia X aparece ANTES de funding/IPO
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.hackernews_stories (
    id SERIAL PRIMARY KEY,

    -- HackerNews identifiers
    story_id BIGINT UNIQUE NOT NULL,
    object_id VARCHAR(100),

    -- Story info
    title TEXT NOT NULL,
    url TEXT,
    author VARCHAR(255),

    -- Metrics
    points INT DEFAULT 0,
    num_comments INT DEFAULT 0,

    -- Metadata
    story_type VARCHAR(50), -- story, ask_hn, show_hn, poll
    tags TEXT[],

    -- Timestamps
    created_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Extracted metadata
    is_tech_related BOOLEAN DEFAULT TRUE,
    keywords TEXT[], -- Extracted from title
    mentioned_companies TEXT[], -- Company names extracted from title/url
    mentioned_technologies TEXT[], -- Technologies extracted from title

    -- Índices para queries rápidas
    CONSTRAINT hackernews_stories_story_id_key UNIQUE (story_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_hn_points ON sofia.hackernews_stories(points DESC);
CREATE INDEX IF NOT EXISTS idx_hn_comments ON sofia.hackernews_stories(num_comments DESC);
CREATE INDEX IF NOT EXISTS idx_hn_created ON sofia.hackernews_stories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_hn_author ON sofia.hackernews_stories(author);
CREATE INDEX IF NOT EXISTS idx_hn_keywords ON sofia.hackernews_stories USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_hn_companies ON sofia.hackernews_stories USING GIN(mentioned_companies);
CREATE INDEX IF NOT EXISTS idx_hn_technologies ON sofia.hackernews_stories USING GIN(mentioned_technologies);

-- Comentários
COMMENT ON TABLE sofia.hackernews_stories IS 'Stories do HackerNews - detecta buzz tech antes de virar mainstream';
COMMENT ON COLUMN sofia.hackernews_stories.points IS 'Upvotes - >100 em <24h indica interesse explosivo';
COMMENT ON COLUMN sofia.hackernews_stories.num_comments IS '>50 comments = debate ativo (pode ser polêmico ou muito interessante)';
COMMENT ON COLUMN sofia.hackernews_stories.mentioned_technologies IS 'Tecnologias mencionadas (ex: [React, Rust, WASM])';
