-- Migration: Create space industry tracking tables
-- Tracks: Launches, contracts, missions

CREATE TABLE IF NOT EXISTS sofia.space_industry (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- 'launch', 'contract', 'mission', 'milestone'
    mission_name VARCHAR(200),
    company VARCHAR(100), -- SpaceX, Blue Origin, etc
    launch_date TIMESTAMP,
    launch_site VARCHAR(200),
    rocket_type VARCHAR(100),
    payload_type VARCHAR(100), -- satellite, crew, cargo, etc
    payload_count INTEGER,
    orbit_type VARCHAR(50), -- LEO, GEO, lunar, mars, etc
    status VARCHAR(50), -- 'success', 'failure', 'scheduled', 'in-progress'
    customers TEXT[], -- Array of customers
    contract_value_usd BIGINT, -- For contracts
    country VARCHAR(100),
    description TEXT,
    source VARCHAR(100),
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_space_type ON sofia.space_industry(event_type);
CREATE INDEX IF NOT EXISTS idx_space_company ON sofia.space_industry(company);
CREATE INDEX IF NOT EXISTS idx_space_date ON sofia.space_industry(launch_date);
CREATE INDEX IF NOT EXISTS idx_space_status ON sofia.space_industry(status);

-- Add comment
COMMENT ON TABLE sofia.space_industry IS 'Space industry tracking: launches, contracts, missions, milestones';
