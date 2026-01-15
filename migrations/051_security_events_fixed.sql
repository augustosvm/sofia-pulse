-- Security Events: Fixed materialized views with MAX(event_date) window
-- Migration: 051_security_events_fixed.sql
-- Date: 2026-01-15
-- Fix: Use MAX(event_date) instead of CURRENT_DATE for time windows

-- Drop existing views
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_geo_points_30d CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_geo_points CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_momentum CASCADE;

-- Materialized View 1: Country summary (90-day window based on MAX date)
CREATE MATERIALIZED VIEW sofia.mv_security_country_summary AS
WITH dataset_meta AS (
    SELECT MAX(event_date) AS as_of_date
    FROM sofia.security_events
),
raw_stats AS (
    SELECT
        COALESCE(country_code, 'XX') as country_code,
        country_name,
        COUNT(*) as incidents,
        SUM(COALESCE(fatalities, 0)) as fatalities,
        MODE() WITHIN GROUP (ORDER BY event_type) as top_event_type,
        MAX(event_date) as last_event_date
    FROM sofia.security_events, dataset_meta
    WHERE event_date >= (dataset_meta.as_of_date - INTERVAL '90 days')
      AND country_name IS NOT NULL
    GROUP BY country_code, country_name
),
severity_calc AS (
    SELECT
        *,
        (incidents + (fatalities * 3.0)) as severity_raw
    FROM raw_stats
),
p95_calc AS (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY severity_raw) as p95_value
    FROM severity_calc
),
normalized AS (
    SELECT
        s.*,
        CASE
            WHEN p.p95_value > 0 THEN LEAST(100, ROUND((s.severity_raw / p.p95_value) * 100))
            ELSE 0
        END as severity_norm
    FROM severity_calc s, p95_calc p
)
SELECT
    country_code,
    country_name,
    incidents,
    fatalities,
    severity_raw,
    severity_norm,
    CASE
        WHEN severity_norm >= 80 THEN 'Critical'
        WHEN severity_norm >= 60 THEN 'High'
        WHEN severity_norm >= 40 THEN 'Elevated'
        WHEN severity_norm >= 20 THEN 'Moderate'
        ELSE 'Low'
    END as risk_level,
    top_event_type,
    last_event_date,
    90 as window_days,
    'ACLED' as data_source,
    (SELECT as_of_date FROM dataset_meta) as as_of_date,
    now() as last_updated
FROM normalized;

CREATE INDEX idx_mv_security_country_summary_code
    ON sofia.mv_security_country_summary(country_code);
CREATE INDEX idx_mv_security_country_summary_severity
    ON sofia.mv_security_country_summary(severity_norm DESC);

-- Materialized View 2: Geo points (90-day window based on MAX date)
CREATE MATERIALIZED VIEW sofia.mv_security_geo_points AS
WITH dataset_meta AS (
    SELECT MAX(event_date) AS as_of_date
    FROM sofia.security_events
),
raw_points AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY latitude, longitude) as id,
        latitude,
        longitude,
        COALESCE(country_code, 'XX') as country_code,
        country_name,
        COUNT(*) as incidents,
        SUM(COALESCE(fatalities, 0)) as fatalities,
        MODE() WITHIN GROUP (ORDER BY event_type) as top_event_type
    FROM sofia.security_events, dataset_meta
    WHERE event_date >= (dataset_meta.as_of_date - INTERVAL '90 days')
      AND latitude IS NOT NULL
      AND longitude IS NOT NULL
    GROUP BY latitude, longitude, country_code, country_name
),
severity_calc AS (
    SELECT
        *,
        (incidents + (fatalities * 3.0)) as severity_raw
    FROM raw_points
),
p95_calc AS (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY severity_raw) as p95_value
    FROM severity_calc
),
normalized AS (
    SELECT
        s.*,
        CASE
            WHEN p.p95_value > 0 THEN LEAST(100, ROUND((s.severity_raw / p.p95_value) * 100))
            ELSE 0
        END as severity_norm
    FROM severity_calc s, p95_calc p
)
SELECT
    id,
    country_name,
    country_code,
    latitude,
    longitude,
    incidents,
    fatalities,
    severity_raw,
    severity_norm,
    CASE
        WHEN severity_norm >= 80 THEN 'Critical'
        WHEN severity_norm >= 60 THEN 'High'
        WHEN severity_norm >= 40 THEN 'Elevated'
        WHEN severity_norm >= 20 THEN 'Moderate'
        ELSE 'Low'
    END as risk_level,
    top_event_type,
    90 as window_days,
    'ACLED' as data_source,
    (SELECT as_of_date FROM dataset_meta) as as_of_date,
    now() as last_updated
FROM normalized;

CREATE INDEX idx_mv_security_geo_severity
    ON sofia.mv_security_geo_points(severity_norm DESC);

-- Materialized View 3: Momentum (90d current vs 90d previous)
CREATE MATERIALIZED VIEW sofia.mv_security_momentum AS
WITH dataset_meta AS (
    SELECT MAX(event_date) AS as_of_date
    FROM sofia.security_events
),
stats AS (
    SELECT
        COALESCE(country_code, 'XX') as country_code,
        country_name,
        COUNT(*) FILTER (
            WHERE event_date >= (SELECT as_of_date FROM dataset_meta) - INTERVAL '90 days'
        ) as incidents_current_window,
        COUNT(*) FILTER (
            WHERE event_date >= (SELECT as_of_date FROM dataset_meta) - INTERVAL '180 days'
              AND event_date < (SELECT as_of_date FROM dataset_meta) - INTERVAL '90 days'
        ) as incidents_prev_window
    FROM sofia.security_events, dataset_meta
    WHERE country_name IS NOT NULL
    GROUP BY country_code, country_name
)
SELECT
    country_code,
    country_name,
    incidents_current_window,
    incidents_prev_window,
    (incidents_current_window - incidents_prev_window) as delta_abs,
    CASE
        WHEN incidents_prev_window = 0 AND incidents_current_window > 0 THEN 100
        WHEN incidents_prev_window > 0 THEN
            ROUND(100.0 * (incidents_current_window - incidents_prev_window) / incidents_prev_window)
        ELSE 0
    END as delta_pct,
    CASE
        WHEN incidents_current_window > incidents_prev_window THEN 'up'
        WHEN incidents_current_window < incidents_prev_window THEN 'down'
        ELSE 'flat'
    END as trend,
    90 as window_days,
    'ACLED' as data_source,
    (SELECT as_of_date FROM dataset_meta) as as_of_date,
    now() as last_updated
FROM stats
WHERE incidents_current_window > 0 OR incidents_prev_window > 0;

CREATE INDEX idx_mv_security_momentum_code
    ON sofia.mv_security_momentum(country_code);
CREATE INDEX idx_mv_security_momentum_delta
    ON sofia.mv_security_momentum(delta_pct DESC);

-- Refresh function
CREATE OR REPLACE FUNCTION sofia.refresh_security_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_summary;
    REFRESH MATERIALIZED VIEW sofia.mv_security_geo_points;
    REFRESH MATERIALIZED VIEW sofia.mv_security_momentum;
END;
$$ LANGUAGE plpgsql;

COMMENT ON MATERIALIZED VIEW sofia.mv_security_country_summary IS 'Country-level security summary (90d window from MAX event_date)';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_geo_points IS 'Geolocated security hotspots (90d window from MAX event_date)';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_momentum IS 'Security trend momentum (current 90d vs previous 90d)';
