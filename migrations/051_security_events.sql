-- Security Events: Unified table for ACLED + GDELT geopolitical risk data
-- Migration: 051_security_events.sql

-- Create canonical security_events table
CREATE TABLE IF NOT EXISTS sofia.security_events (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,                          -- 'ACLED' | 'GDELT'
    source_id TEXT NOT NULL,                       -- unique per source
    event_date DATE NOT NULL,
    week_start DATE NULL,                          -- for ACLED weekly aggregates
    country_name TEXT NULL,
    country_code TEXT NULL,                        -- ISO2 preferred
    country_id BIGINT NULL,                        -- FK -> countries.id
    admin1 TEXT NULL,                              -- state/province
    city TEXT NULL,
    latitude DOUBLE PRECISION NULL,
    longitude DOUBLE PRECISION NULL,
    event_type TEXT NULL,
    sub_event_type TEXT NULL,
    severity_score DOUBLE PRECISION NULL,          -- always fill (even proxy)
    fatalities INTEGER NULL,
    event_count INTEGER NULL,                      -- for aggregated data
    raw_payload JSONB NOT NULL,
    source_url TEXT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_security_source_id UNIQUE(source, source_id)
);

-- Indexes for map queries
CREATE INDEX IF NOT EXISTS idx_security_event_date ON sofia.security_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_security_country_id ON sofia.security_events(country_id);
CREATE INDEX IF NOT EXISTS idx_security_country_code ON sofia.security_events(country_code);
CREATE INDEX IF NOT EXISTS idx_security_source ON sofia.security_events(source);
CREATE INDEX IF NOT EXISTS idx_security_geo ON sofia.security_events(latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Materialized View 1: Country summary for choropleth map
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_security_country_summary AS
SELECT
    country_code,
    country_id,
    country_name,
    COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '7 days') as incidents_7d,
    COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days') as incidents_30d,
    COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '90 days') as incidents_90d,
    COALESCE(SUM(severity_score) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'), 0) as severity_30d,
    COALESCE(SUM(fatalities) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'), 0) as fatalities_30d,
    COALESCE(SUM(event_count) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'), 0) as total_events_30d,
    MODE() WITHIN GROUP (ORDER BY event_type) as top_event_type,
    MAX(event_date) as last_event_date,
    now() as last_updated
FROM sofia.security_events
WHERE country_code IS NOT NULL
GROUP BY country_code, country_id, country_name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_security_country_code
    ON sofia.mv_security_country_summary(country_code);

-- Materialized View 2: Geo points for hotspot markers (last 30 days)
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_security_geo_points_30d AS
SELECT
    latitude,
    longitude,
    country_code,
    country_id,
    SUM(severity_score) as severity_30d,
    COUNT(*) as incidents_30d,
    SUM(COALESCE(fatalities, 0)) as fatalities_30d,
    jsonb_build_object(
        'acled_pct', ROUND(100.0 * COUNT(*) FILTER (WHERE source = 'ACLED') / NULLIF(COUNT(*), 0)),
        'gdelt_pct', ROUND(100.0 * COUNT(*) FILTER (WHERE source = 'GDELT') / NULLIF(COUNT(*), 0))
    ) as source_mix,
    CASE
        WHEN SUM(severity_score) > 100 THEN 'Critical Hotspot'
        WHEN SUM(severity_score) > 50 THEN 'High Risk Zone'
        WHEN SUM(severity_score) > 20 THEN 'Elevated Risk'
        ELSE 'Monitored Area'
    END as label
FROM sofia.security_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
  AND latitude IS NOT NULL
  AND longitude IS NOT NULL
GROUP BY latitude, longitude, country_code, country_id
HAVING COUNT(*) >= 1;

CREATE INDEX IF NOT EXISTS idx_mv_security_geo_severity
    ON sofia.mv_security_geo_points_30d(severity_30d DESC);

-- Materialized View 3: Momentum (30d vs prev 30d)
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_security_momentum AS
SELECT
    country_code,
    country_id,
    country_name,
    COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days') as incidents_last_30d,
    COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '60 days'
                      AND event_date < CURRENT_DATE - INTERVAL '30 days') as incidents_prev_30d,
    CASE
        WHEN COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '60 days'
                              AND event_date < CURRENT_DATE - INTERVAL '30 days') = 0 THEN 100
        ELSE ROUND(
            100.0 * (
                COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days') -
                COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '60 days'
                                  AND event_date < CURRENT_DATE - INTERVAL '30 days')
            ) / NULLIF(COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '60 days'
                                         AND event_date < CURRENT_DATE - INTERVAL '30 days'), 0)
        )
    END as momentum_pct,
    now() as last_updated
FROM sofia.security_events
WHERE country_code IS NOT NULL
GROUP BY country_code, country_id, country_name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_security_momentum_code
    ON sofia.mv_security_momentum(country_code);

-- Refresh function
CREATE OR REPLACE FUNCTION sofia.refresh_security_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_country_summary;
    REFRESH MATERIALIZED VIEW sofia.mv_security_geo_points_30d;
    REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_momentum;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE sofia.security_events IS 'Unified geopolitical risk events from ACLED and GDELT for map visualization';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_country_summary IS 'Country-level security summary for choropleth maps';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_geo_points_30d IS 'Geolocated security hotspots for marker overlay';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_momentum IS 'Security trend momentum by country';
