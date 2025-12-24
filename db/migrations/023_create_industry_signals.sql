-- Create unified table for Industry Signals
CREATE TABLE IF NOT EXISTS sofia.industry_signals (
    id SERIAL PRIMARY KEY,
    
    -- Core identification
    source VARCHAR(50) NOT NULL,           -- 'gdelt', 'nvd', 'github-advisory', 'space-launch', etc.
    external_id VARCHAR(255) NOT NULL,     -- Unique ID in source (CVE-2024-1234, GDELT-EVENT-ID)
    
    -- Content
    title TEXT NOT NULL,
    summary TEXT,                          -- abstract, description, snippet
    url TEXT,                              -- Direct link to source
    
    -- Classification
    category VARCHAR(100),                 -- 'security', 'space', 'geopolitics', 'ai-regulation'
    signal_type VARCHAR(50),               -- 'vulnerability', 'launch', 'event', 'legislation'
    
    -- Metrics
    impact_score DECIMAL(5, 2),            -- 0-10 score (CVSS, Tone, Priority)
    sentiment_score DECIMAL(5, 2),         -- -10 to +10 (GDELT Tone) or similar
    
    -- Flexible metadata for specific fields
    metadata JSONB DEFAULT '{}'::jsonb,    -- Stores actors, rocket_type, affected_products, etc.
    
    -- Time
    published_at TIMESTAMP WITH TIME ZONE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_industry_signal UNIQUE (source, external_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_industry_signals_source ON sofia.industry_signals(source);
CREATE INDEX IF NOT EXISTS idx_industry_signals_category ON sofia.industry_signals(category);
CREATE INDEX IF NOT EXISTS idx_industry_signals_published ON sofia.industry_signals(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_industry_signals_metadata ON sofia.industry_signals USING gin (metadata);

-- View for Cybersecurity (Backwards compatibility)
CREATE OR REPLACE VIEW sofia.cybersecurity_events_view AS
SELECT 
    external_id as event_id,
    title,
    summary as description,
    (metadata->>'severity') as severity,
    impact_score as cvss_score,
    published_at as published_date,
    source,
    url as source_url
FROM sofia.industry_signals
WHERE category = 'security';
