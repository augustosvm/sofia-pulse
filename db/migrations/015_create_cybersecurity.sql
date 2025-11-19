-- Migration: Create cybersecurity tracking tables
-- Tracks: CVEs, data breaches, security advisories

CREATE TABLE IF NOT EXISTS sofia.cybersecurity_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- 'cve', 'breach', 'advisory', 'ransomware'
    event_id VARCHAR(100) UNIQUE, -- CVE-2024-1234, etc
    title TEXT NOT NULL,
    description TEXT,
    severity VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    cvss_score DECIMAL(3,1), -- 0.0 to 10.0
    affected_products TEXT[], -- Array of affected products
    vendors TEXT[], -- Array of vendors
    published_date DATE NOT NULL,
    source VARCHAR(100), -- 'nvd', 'github', 'cisa', etc
    source_url TEXT,
    affected_count INTEGER, -- For breaches: number of records affected
    tags TEXT[], -- Generic tags
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cyber_type ON sofia.cybersecurity_events(event_type);
CREATE INDEX IF NOT EXISTS idx_cyber_severity ON sofia.cybersecurity_events(severity);
CREATE INDEX IF NOT EXISTS idx_cyber_date ON sofia.cybersecurity_events(published_date);
CREATE INDEX IF NOT EXISTS idx_cyber_cvss ON sofia.cybersecurity_events(cvss_score);

-- Add comment
COMMENT ON TABLE sofia.cybersecurity_events IS 'Cybersecurity events: CVEs, breaches, ransomware attacks, security advisories';
