-- Migration: 005_security_map_views.sql
-- Purpose: Create canonical views for Security Map (Points & Summary)
-- Engine: PostgreSQL

BEGIN;

-- 1. Ensure Table Exists (Idempotent check)
CREATE TABLE IF NOT EXISTS sofia.security_events (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_date TIMESTAMP WITH TIME ZONE,
    country_code TEXT,
    country_name TEXT,
    admin1 TEXT,
    admin2 TEXT,
    location_name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    event_type TEXT,
    sub_event_type TEXT,
    fatalities INTEGER DEFAULT 0,
    events INTEGER DEFAULT 1,
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_security_events_source_id UNIQUE (source, event_id)
);

-- Ensure columns exist (for existing tables)
DO $$
BEGIN
    BEGIN
        ALTER TABLE sofia.security_events ADD COLUMN events INTEGER DEFAULT 1;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END;
    BEGIN
        ALTER TABLE sofia.security_events ADD COLUMN raw_payload JSONB;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END;
    BEGIN
        ALTER TABLE sofia.security_events ADD COLUMN country_code TEXT;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END;
END $$;


CREATE INDEX IF NOT EXISTS idx_security_events_source_date ON sofia.security_events(source, event_date DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_country ON sofia.security_events(country_code);
CREATE INDEX IF NOT EXISTS idx_security_events_latlon ON sofia.security_events(latitude, longitude);


-- 2. Canonical Map Points View (mv_security_geo_points)
-- Aggregates events by location (Lat/Lon) for efficient map rendering
-- Windows: 30 days (default) and 90 days

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_geo_points CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_geo_points AS
WITH recent_events AS (
    SELECT 
        country_code,
        country_name,
        latitude,
        longitude,
        event_type,
        fatalities,
        events,
        event_date
    FROM sofia.security_events
    WHERE source IN ('ACLED', 'HDX_HAPI_ACLED', 'ACLED_AGGREGATED') 
      AND latitude IS NOT NULL 
      AND longitude IS NOT NULL
      AND event_date >= (CURRENT_DATE - INTERVAL '90 days')
)
SELECT
    -- Deterministic ID for the point cluster
    md5(COALESCE(country_code, '') || latitude::text || longitude::text) AS point_id,
    country_code,
    country_name,
    latitude,
    longitude,
    
    -- 30 Days Metrics
    COUNT(*) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '30 days')) AS incidents_30d,
    SUM(fatalities) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '30 days')) AS fatalities_30d,
    (
        COUNT(*) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '30 days')) + 
        (SUM(fatalities) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '30 days')) * 3)
    )::INTEGER AS severity_30d,
    
    -- 90 Days Metrics
    COUNT(*) AS incidents_90d,
    SUM(fatalities) AS fatalities_90d,
    (COUNT(*) + (SUM(fatalities) * 3))::INTEGER AS severity_90d,
    
    -- Top Event Type (Simple Mode approximation via Max)
    -- In a real scenario we might want a subquery for mode, but max() or simple aggregation is faster for MV
    (SELECT mode() WITHIN GROUP (ORDER BY event_type) FROM recent_events sub WHERE sub.latitude = recent_events.latitude AND sub.longitude = recent_events.longitude AND sub.event_date >= (CURRENT_DATE - INTERVAL '30 days')) AS top_event_type_30d

FROM recent_events
GROUP BY country_code, country_name, latitude, longitude;

CREATE INDEX idx_mv_sec_points_latlon ON sofia.mv_security_geo_points(latitude, longitude);
CREATE INDEX idx_mv_sec_points_severity ON sofia.mv_security_geo_points(severity_30d DESC);
CREATE INDEX idx_mv_sec_points_country ON sofia.mv_security_geo_points(country_code);


-- 3. Country Summary View (mv_security_country_summary)
-- High-level stats for Cards and Ranking

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_summary CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_country_summary AS
WITH period_stats AS (
    SELECT
        country_code,
        country_name,
        -- Current Period (Last 30d)
        COUNT(*) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '30 days')) AS incidents_30d,
        SUM(fatalities) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '30 days')) AS fatalities_30d,
        
        -- Previous Period (30d to 60d ago) for Momentum
        COUNT(*) FILTER (WHERE event_date >= (CURRENT_DATE - INTERVAL '60 days') AND event_date < (CURRENT_DATE - INTERVAL '30 days')) AS incidents_prev_30d
    FROM sofia.security_events
    WHERE source IN ('ACLED', 'HDX_HAPI_ACLED', 'ACLED_AGGREGATED')
    GROUP BY country_code, country_name
)
SELECT
    country_code,
    country_name,
    incidents_30d,
    fatalities_30d,
    (incidents_30d + (fatalities_30d * 3))::INTEGER AS severity_30d,
    
    -- Momentum Calculation (Growth %)
    CASE 
        WHEN incidents_prev_30d = 0 THEN 0 
        ELSE ROUND(((incidents_30d - incidents_prev_30d)::numeric / incidents_prev_30d) * 100, 1)
    END AS momentum_pct
FROM period_stats
WHERE incidents_30d > 0;

CREATE INDEX idx_mv_sec_country_severity ON sofia.mv_security_country_summary(severity_30d DESC);

COMMIT;
