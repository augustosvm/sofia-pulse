-- Security Hybrid Model: ACLED + GDELT + Structural Signals
-- Migration: 052_security_hybrid_model.sql
-- Date: 2026-01-15
-- Purpose: Canonical observation model with country dimension

-- ============================================================================
-- 1. Country Dimension (static reference)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.dim_country (
    country_code VARCHAR(3) PRIMARY KEY, -- ISO3 as primary
    country_name VARCHAR(200) NOT NULL,
    iso2 VARCHAR(2),
    iso3 VARCHAR(3),
    continent VARCHAR(50),
    region VARCHAR(100),
    centroid_lat DECIMAL(10, 6),
    centroid_lon DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dim_country_name ON sofia.dim_country(country_name);
CREATE INDEX idx_dim_country_continent ON sofia.dim_country(continent);
CREATE INDEX idx_dim_country_region ON sofia.dim_country(region);

COMMENT ON TABLE sofia.dim_country IS 'Country dimension with ISO codes, continent, region, and centroid coordinates';

-- ============================================================================
-- 2. Canonical Security Observations Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.security_observations (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- 'ACLED', 'GDELT', 'WORLD_BANK'
    signal_type VARCHAR(50) NOT NULL, -- 'INCIDENT', 'STRUCTURAL'
    event_time_start TIMESTAMP,
    event_time_end TIMESTAMP,
    country_code VARCHAR(3) NOT NULL,
    admin1 VARCHAR(100), -- State/province
    admin2 VARCHAR(100), -- City/district
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    metric_name VARCHAR(100) NOT NULL, -- 'incidents', 'fatalities', 'gdelt_instability', 'unemployment', etc.
    metric_value DECIMAL(18, 4),
    severity_raw DECIMAL(18, 4),
    severity_norm DECIMAL(5, 2), -- 0-100 normalized within source/signal_type
    as_of_date DATE NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB, -- Flexible storage for source-specific fields
    CONSTRAINT fk_country FOREIGN KEY (country_code) REFERENCES sofia.dim_country(country_code)
);

-- Indexes for performance
CREATE INDEX idx_security_obs_country_time ON sofia.security_observations(country_code, event_time_start);
CREATE INDEX idx_security_obs_source_signal ON sofia.security_observations(source, signal_type);
CREATE INDEX idx_security_obs_signal_severity ON sofia.security_observations(signal_type, severity_norm DESC);
CREATE INDEX idx_security_obs_as_of_date ON sofia.security_observations(as_of_date DESC);
CREATE INDEX idx_security_obs_coords ON sofia.security_observations(latitude, longitude) WHERE latitude IS NOT NULL;

COMMENT ON TABLE sofia.security_observations IS 'Canonical security observations from all sources (ACLED, GDELT, World Bank)';
COMMENT ON COLUMN sofia.security_observations.signal_type IS 'INCIDENT (dynamic) or STRUCTURAL (slow-moving)';
COMMENT ON COLUMN sofia.security_observations.severity_norm IS 'Normalized 0-100 within source/signal_type (not comparable across types without weighting)';

-- ============================================================================
-- 3. Materialized Views: Country-Level Aggregations
-- ============================================================================

-- 3.1 ACLED Country Summary (from existing data)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_acled CASCADE;
CREATE MATERIALIZED VIEW sofia.mv_security_country_acled AS
WITH dataset_meta AS (
    SELECT MAX(event_date) AS as_of_date
    FROM sofia.security_events
),
raw_stats AS (
    SELECT
        COALESCE(country_code, 'XXX') as country_code,
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

CREATE INDEX idx_mv_acled_country_code ON sofia.mv_security_country_acled(country_code);
CREATE INDEX idx_mv_acled_severity ON sofia.mv_security_country_acled(severity_norm DESC);

-- 3.2 GDELT Country Summary (placeholder - will be populated by collector)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_gdelt CASCADE;
CREATE MATERIALIZED VIEW sofia.mv_security_country_gdelt AS
SELECT
    country_code,
    MAX(metric_value) as instability_score,
    MAX(severity_norm) as severity_norm,
    CASE
        WHEN MAX(severity_norm) >= 80 THEN 'Critical'
        WHEN MAX(severity_norm) >= 60 THEN 'High'
        WHEN MAX(severity_norm) >= 40 THEN 'Elevated'
        WHEN MAX(severity_norm) >= 20 THEN 'Moderate'
        ELSE 'Low'
    END as risk_level,
    MAX(as_of_date) as as_of_date,
    COUNT(*) as event_count,
    'GDELT' as data_source,
    now() as last_updated
FROM sofia.security_observations
WHERE source = 'GDELT' AND signal_type = 'INCIDENT'
GROUP BY country_code;

CREATE INDEX idx_mv_gdelt_country_code ON sofia.mv_security_country_gdelt(country_code);
CREATE INDEX idx_mv_gdelt_severity ON sofia.mv_security_country_gdelt(severity_norm DESC);

-- 3.3 Structural Risk (World Bank + other slow signals)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_structural_risk_country CASCADE;
CREATE MATERIALIZED VIEW sofia.mv_structural_risk_country AS
WITH latest_structural AS (
    SELECT
        country_code,
        metric_name,
        metric_value,
        severity_norm,
        as_of_date,
        ROW_NUMBER() OVER (PARTITION BY country_code, metric_name ORDER BY as_of_date DESC) as rn
    FROM sofia.security_observations
    WHERE source = 'WORLD_BANK' AND signal_type = 'STRUCTURAL'
),
pivoted AS (
    SELECT
        country_code,
        MAX(CASE WHEN metric_name = 'unemployment' THEN metric_value END) as unemployment,
        MAX(CASE WHEN metric_name = 'unemployment' THEN severity_norm END) as unemployment_norm,
        MAX(CASE WHEN metric_name = 'inflation' THEN metric_value END) as inflation,
        MAX(CASE WHEN metric_name = 'inflation' THEN severity_norm END) as inflation_norm,
        MAX(CASE WHEN metric_name = 'governance' THEN metric_value END) as governance,
        MAX(CASE WHEN metric_name = 'governance' THEN severity_norm END) as governance_norm,
        MAX(as_of_date) as as_of_date
    FROM latest_structural
    WHERE rn = 1
    GROUP BY country_code
)
SELECT
    country_code,
    unemployment,
    inflation,
    governance,
    -- Composite structural severity (average of normalized components)
    ROUND((COALESCE(unemployment_norm, 0) + COALESCE(inflation_norm, 0) + COALESCE(governance_norm, 0)) /
          NULLIF(
              (CASE WHEN unemployment_norm IS NOT NULL THEN 1 ELSE 0 END +
               CASE WHEN inflation_norm IS NOT NULL THEN 1 ELSE 0 END +
               CASE WHEN governance_norm IS NOT NULL THEN 1 ELSE 0 END), 0
          ), 2) as severity_norm,
    CASE
        WHEN ROUND((COALESCE(unemployment_norm, 0) + COALESCE(inflation_norm, 0) + COALESCE(governance_norm, 0)) /
             NULLIF(
                 (CASE WHEN unemployment_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN inflation_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN governance_norm IS NOT NULL THEN 1 ELSE 0 END), 0
             ), 2) >= 80 THEN 'Critical'
        WHEN ROUND((COALESCE(unemployment_norm, 0) + COALESCE(inflation_norm, 0) + COALESCE(governance_norm, 0)) /
             NULLIF(
                 (CASE WHEN unemployment_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN inflation_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN governance_norm IS NOT NULL THEN 1 ELSE 0 END), 0
             ), 2) >= 60 THEN 'High'
        WHEN ROUND((COALESCE(unemployment_norm, 0) + COALESCE(inflation_norm, 0) + COALESCE(governance_norm, 0)) /
             NULLIF(
                 (CASE WHEN unemployment_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN inflation_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN governance_norm IS NOT NULL THEN 1 ELSE 0 END), 0
             ), 2) >= 40 THEN 'Elevated'
        WHEN ROUND((COALESCE(unemployment_norm, 0) + COALESCE(inflation_norm, 0) + COALESCE(governance_norm, 0)) /
             NULLIF(
                 (CASE WHEN unemployment_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN inflation_norm IS NOT NULL THEN 1 ELSE 0 END +
                  CASE WHEN governance_norm IS NOT NULL THEN 1 ELSE 0 END), 0
             ), 2) >= 20 THEN 'Moderate'
        ELSE 'Low'
    END as risk_level,
    JSONB_BUILD_OBJECT(
        'unemployment', unemployment_norm,
        'inflation', inflation_norm,
        'governance', governance_norm
    ) as component_scores,
    as_of_date,
    'WORLD_BANK' as data_source,
    now() as last_updated
FROM pivoted;

CREATE INDEX idx_mv_structural_country_code ON sofia.mv_structural_risk_country(country_code);
CREATE INDEX idx_mv_structural_severity ON sofia.mv_structural_risk_country(severity_norm DESC);

-- 3.4 Combined Country Risk (Hybrid Model)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_combined CASCADE;
CREATE MATERIALIZED VIEW sofia.mv_security_country_combined AS
WITH acute AS (
    SELECT
        COALESCE(a.country_code, g.country_code) as country_code,
        GREATEST(COALESCE(a.severity_norm, 0), COALESCE(g.severity_norm, 0)) as acute_severity,
        COALESCE(a.severity_norm, 0) as acled_severity,
        COALESCE(g.severity_norm, 0) as gdelt_severity,
        a.incidents as acled_incidents,
        a.fatalities as acled_fatalities,
        g.event_count as gdelt_events,
        a.as_of_date as acled_date,
        g.as_of_date as gdelt_date
    FROM sofia.mv_security_country_acled a
    FULL OUTER JOIN sofia.mv_security_country_gdelt g ON a.country_code = g.country_code
),
combined AS (
    SELECT
        a.country_code,
        c.country_name,
        c.continent,
        c.region,
        a.acute_severity,
        a.acled_severity,
        a.gdelt_severity,
        COALESCE(s.severity_norm, 0) as structural_severity,
        -- Weighted total risk: 65% Acute + 35% Structural
        ROUND((a.acute_severity * 0.65) + (COALESCE(s.severity_norm, 0) * 0.35), 2) as total_risk,
        CASE
            WHEN ROUND((a.acute_severity * 0.65) + (COALESCE(s.severity_norm, 0) * 0.35), 2) >= 80 THEN 'Critical'
            WHEN ROUND((a.acute_severity * 0.65) + (COALESCE(s.severity_norm, 0) * 0.35), 2) >= 60 THEN 'High'
            WHEN ROUND((a.acute_severity * 0.65) + (COALESCE(s.severity_norm, 0) * 0.35), 2) >= 40 THEN 'Elevated'
            WHEN ROUND((a.acute_severity * 0.65) + (COALESCE(s.severity_norm, 0) * 0.35), 2) >= 20 THEN 'Moderate'
            ELSE 'Low'
        END as risk_level,
        a.acled_incidents,
        a.acled_fatalities,
        a.gdelt_events,
        s.unemployment,
        s.inflation,
        s.governance,
        s.component_scores as structural_components,
        JSONB_BUILD_OBJECT(
            'acute_weight', 0.65,
            'structural_weight', 0.35,
            'formula', 'total_risk = (acute_severity * 0.65) + (structural_severity * 0.35)'
        ) as scoring_methodology,
        c.centroid_lat,
        c.centroid_lon,
        GREATEST(a.acled_date, a.gdelt_date, s.as_of_date) as as_of_date,
        now() as last_updated
    FROM acute a
    LEFT JOIN sofia.dim_country c ON a.country_code = c.country_code
    LEFT JOIN sofia.mv_structural_risk_country s ON a.country_code = s.country_code
)
SELECT * FROM combined;

CREATE INDEX idx_mv_combined_country_code ON sofia.mv_security_country_combined(country_code);
CREATE INDEX idx_mv_combined_total_risk ON sofia.mv_security_country_combined(total_risk DESC);
CREATE INDEX idx_mv_combined_continent ON sofia.mv_security_country_combined(continent);

-- ============================================================================
-- 4. Refresh Function
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.refresh_security_hybrid_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_acled;
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_gdelt;
    REFRESH MATERIALIZED VIEW sofia.mv_structural_risk_country;
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_combined;

    -- Also refresh existing geo view
    REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_geo_points;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.refresh_security_hybrid_views() IS 'Refresh all security hybrid model views (ACLED + GDELT + Structural + Combined)';
