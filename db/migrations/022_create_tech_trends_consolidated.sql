CREATE TABLE IF NOT EXISTS sofia.tech_trends (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,       -- 'github', 'stackoverflow', 'npm', 'pypi', 'reddit'
    name VARCHAR(255) NOT NULL,        -- 'react', 'python', 'kubernetes'
    category VARCHAR(100),             -- 'language', 'framework', 'library'
    trend_type VARCHAR(50),            -- 'repository', 'tag', 'package'
    
    -- Metrics
    score NUMERIC(15, 2),              -- Main unified metric (stars, downloads, count)
    rank INTEGER,
    
    -- Specifics
    stars INTEGER,
    forks INTEGER,
    views INTEGER,
    mentions INTEGER,
    growth_rate NUMERIC(10, 2),
    
    -- Time Context
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Extra
    metadata JSONB,
    
    -- Constraints
    CONSTRAINT unique_tech_trend UNIQUE (source, name, period_start)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tech_trends_source ON sofia.tech_trends(source);
CREATE INDEX IF NOT EXISTS idx_tech_trends_name ON sofia.tech_trends(name);
CREATE INDEX IF NOT EXISTS idx_tech_trends_period ON sofia.tech_trends(period_start);
CREATE INDEX IF NOT EXISTS idx_tech_trends_score ON sofia.tech_trends(score DESC);
CREATE INDEX IF NOT EXISTS idx_tech_trends_metadata ON sofia.tech_trends USING GIN(metadata);
