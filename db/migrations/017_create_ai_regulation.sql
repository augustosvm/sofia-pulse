-- Migration: Create AI regulation tracking table
-- Tracks: AI laws, regulations, compliance requirements, policy updates

CREATE TABLE IF NOT EXISTS sofia.ai_regulation (
    id SERIAL PRIMARY KEY,
    regulation_type VARCHAR(50) NOT NULL, -- 'law', 'guideline', 'policy', 'enforcement'
    title TEXT NOT NULL,
    jurisdiction VARCHAR(100), -- 'EU', 'Brazil', 'USA', 'China', 'Global', etc
    regulatory_body VARCHAR(200), -- 'European Commission', 'ANPD', 'FTC', etc
    status VARCHAR(50), -- 'proposed', 'draft', 'enacted', 'enforced'
    effective_date DATE,
    announced_date DATE,
    scope TEXT[], -- ['AI systems', 'facial recognition', 'data privacy', etc]
    impact_level VARCHAR(20), -- 'high', 'medium', 'low'
    penalties_max BIGINT, -- Maximum penalty in USD
    description TEXT,
    key_requirements TEXT[],
    affected_sectors TEXT[], -- ['tech', 'healthcare', 'finance', etc]
    source VARCHAR(100),
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, jurisdiction)
);

CREATE INDEX IF NOT EXISTS idx_reg_type ON sofia.ai_regulation(regulation_type);
CREATE INDEX IF NOT EXISTS idx_reg_jurisdiction ON sofia.ai_regulation(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_reg_status ON sofia.ai_regulation(status);
CREATE INDEX IF NOT EXISTS idx_reg_date ON sofia.ai_regulation(announced_date);

-- Add comment
COMMENT ON TABLE sofia.ai_regulation IS 'AI regulation tracking: laws, policies, compliance requirements';
