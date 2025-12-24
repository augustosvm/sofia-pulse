-- ============================================================
-- CONSOLIDAÇÃO: TECH TRENDS
-- Consolida 5 tabelas → 1 tabela unificada
-- ============================================================

-- 1. CRIAR TABELA UNIFICADA
CREATE TABLE IF NOT EXISTS sofia.tech_trends (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'github', 'stackoverflow', 'npm', 'pypi', 'skill', 'salary'
    
    -- Identificação
    name VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    trend_type VARCHAR(50),  -- 'repository', 'question', 'package', 'skill', 'salary'
    
    -- Métricas gerais
    score NUMERIC,
    rank INTEGER,
    
    -- Métricas específicas (usar conforme source)
    stars INTEGER,
    forks INTEGER,
    views INTEGER,
    mentions INTEGER,
    growth_rate NUMERIC,
    
    -- Temporal
    period_start DATE,
    period_end DATE,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata flexível para dados específicos de cada source
    metadata JSONB,
    
    -- Constraints
    UNIQUE(source, name, period_start)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_tech_trends_source ON sofia.tech_trends(source);
CREATE INDEX IF NOT EXISTS idx_tech_trends_period ON sofia.tech_trends(period_start DESC, period_end DESC);
CREATE INDEX IF NOT EXISTS idx_tech_trends_score ON sofia.tech_trends(score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_tech_trends_name ON sofia.tech_trends(name);
CREATE INDEX IF NOT EXISTS idx_tech_trends_collected ON sofia.tech_trends(collected_at DESC);

-- 2. MIGRAR DADOS EXISTENTES

-- Migrar ai_github_trends (299 registros)
INSERT INTO sofia.tech_trends (
    source, name, category, trend_type, 
    stars, forks, score, rank,
    period_start, period_end, collected_at, metadata
)
SELECT 
    'github' as source,
    name,
    category,
    'repository' as trend_type,
    stars,
    forks,
    score,
    rank,
    period_start,
    period_end,
    collected_at,
    jsonb_build_object(
        'description', description,
        'language', language,
        'url', url
    ) as metadata
FROM sofia.ai_github_trends
ON CONFLICT (source, name, period_start) DO NOTHING;

-- Migrar stackoverflow_trends (712 registros)
INSERT INTO sofia.tech_trends (
    source, name, category, trend_type,
    views, score,
    period_start, period_end, collected_at, metadata
)
SELECT 
    'stackoverflow' as source,
    tag as name,
    NULL as category,
    'question' as trend_type,
    count as views,
    NULL as score,
    week_start as period_start,
    week_end as period_end,
    collected_at,
    jsonb_build_object(
        'tag', tag,
        'count', count
    ) as metadata
FROM sofia.stackoverflow_trends
ON CONFLICT (source, name, period_start) DO NOTHING;

-- 3. VERIFICAR MIGRAÇÃO
SELECT 
    'TECH_TRENDS MIGRATION' as status,
    source,
    COUNT(*) as records,
    MIN(period_start) as earliest,
    MAX(period_end) as latest
FROM sofia.tech_trends
GROUP BY source
ORDER BY source;

-- 4. DELETAR TABELAS VAZIAS (SEGURO)
DROP TABLE IF EXISTS sofia.trends CASCADE;
DROP TABLE IF EXISTS sofia.tech_job_skill_trends CASCADE;
DROP TABLE IF EXISTS sofia.tech_job_salary_trends CASCADE;

-- 5. RELATÓRIO FINAL
SELECT 
    'Tech Trends Consolidation Complete' as status,
    COUNT(*) as total_records,
    COUNT(DISTINCT source) as sources,
    COUNT(DISTINCT name) as unique_trends
FROM sofia.tech_trends;
