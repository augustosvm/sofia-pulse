-- GDELT Events (Geopolitical events affecting tech/markets)
CREATE TABLE IF NOT EXISTS sofia.gdelt_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    event_date DATE NOT NULL,
    event_time TIMESTAMP,

    -- Actors
    actor1_name VARCHAR(500),
    actor1_country VARCHAR(10),
    actor2_name VARCHAR(500),
    actor2_country VARCHAR(10),

    -- Event details
    event_code VARCHAR(10),
    event_base_code VARCHAR(10),
    event_root_code VARCHAR(10),
    quad_class INT,
    goldstein_scale DECIMAL(5,2),
    num_mentions INT DEFAULT 0,
    num_sources INT DEFAULT 0,
    num_articles INT DEFAULT 0,
    avg_tone DECIMAL(6,3),

    -- Location
    action_geo_country VARCHAR(10),
    action_geo_lat DECIMAL(10,6),
    action_geo_lon DECIMAL(10,6),
    action_geo_fullname TEXT,

    -- Categorization
    categories TEXT[],
    is_tech_related BOOLEAN DEFAULT FALSE,
    is_market_relevant BOOLEAN DEFAULT FALSE,

    -- URLs
    source_url TEXT,

    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gdelt_date ON sofia.gdelt_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_gdelt_countries ON sofia.gdelt_events(actor1_country, actor2_country);
CREATE INDEX IF NOT EXISTS idx_gdelt_goldstein ON sofia.gdelt_events(goldstein_scale);
CREATE INDEX IF NOT EXISTS idx_gdelt_tone ON sofia.gdelt_events(avg_tone);
CREATE INDEX IF NOT EXISTS idx_gdelt_categories ON sofia.gdelt_events USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_gdelt_tech ON sofia.gdelt_events(is_tech_related) WHERE is_tech_related = TRUE;

COMMENT ON TABLE sofia.gdelt_events IS 'Eventos geopolíticos do GDELT que impactam tech e mercados';
