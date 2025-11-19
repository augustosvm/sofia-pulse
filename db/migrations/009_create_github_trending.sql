-- ============================================================================
-- Migration: GitHub Trending Table
-- ============================================================================
-- Collector: collect-github-trending.ts
-- Fonte: GitHub API (https://api.github.com)
-- Frequência: Diário, 08:00 UTC
--
-- Objetivo: Capturar repositórios em trending para detectar tecnologias
--           emergentes ANTES de virarem mainstream (6-12 meses de lead)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.github_trending (
    id SERIAL PRIMARY KEY,

    -- GitHub identifiers
    repo_id BIGINT UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    owner VARCHAR(255),
    name VARCHAR(255),

    -- Repository info
    description TEXT,
    homepage VARCHAR(500),
    language VARCHAR(50),

    -- Metrics (absolutos)
    stars INT DEFAULT 0,
    forks INT DEFAULT 0,
    watchers INT DEFAULT 0,
    open_issues INT DEFAULT 0,

    -- Metrics de crescimento
    stars_today INT DEFAULT 0,
    stars_week INT DEFAULT 0,
    stars_month INT DEFAULT 0,

    -- Metadata
    topics TEXT[],
    license VARCHAR(100),
    is_fork BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    pushed_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Índices para queries rápidas
    CONSTRAINT github_trending_repo_id_key UNIQUE (repo_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_github_trending_language ON sofia.github_trending(language);
CREATE INDEX IF NOT EXISTS idx_github_trending_stars ON sofia.github_trending(stars DESC);
CREATE INDEX IF NOT EXISTS idx_github_trending_stars_week ON sofia.github_trending(stars_week DESC);
CREATE INDEX IF NOT EXISTS idx_github_trending_collected ON sofia.github_trending(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_github_trending_topics ON sofia.github_trending USING GIN(topics);

-- Comentários
COMMENT ON TABLE sofia.github_trending IS 'Repositórios em trending no GitHub - detecta tecnologias emergentes';
COMMENT ON COLUMN sofia.github_trending.stars_week IS 'Crescimento de stars nos últimos 7 dias (weak signal indicator)';
COMMENT ON COLUMN sofia.github_trending.topics IS 'Tags/tópicos do repo (ex: [ai, machine-learning, python])';
