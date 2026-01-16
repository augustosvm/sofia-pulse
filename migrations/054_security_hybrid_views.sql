-- Security Hybrid Model - Materialized Views
-- Migration: 054_security_hybrid_views.sql
-- Date: 2026-01-15

-- ============================================================================
-- 1. ACLED COUNTRY SUMMARY
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_acled CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_country_acled AS
SELECT
    country_code,
    country_name,
    COUNT(*) as incidents,
    SUM(fatalities) as fatalities,
    AVG(severity_norm) as severity_norm,
    MAX(event_time_start) as last_event_date,
    'ACLED' as data_source,
    MAX(collected_at) as as_of_date
FROM sofia.security_observations
WHERE source = 'ACLED'
  AND event_time_start >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY country_code, country_name;

CREATE INDEX idx_mv_acled_country_code ON sofia.mv_security_country_acled(country_code);
CREATE INDEX idx_mv_acled_severity ON sofia.mv_security_country_acled(severity_norm DESC);

-- ============================================================================
-- 2. GDELT COUNTRY SUMMARY
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_gdelt CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_country_gdelt AS
SELECT
    country_code,
    country_name,
    COUNT(*) as incidents,
    AVG(severity_norm) as severity_norm,
    MAX(event_time_start) as last_event_date,
    'GDELT' as data_source,
    MAX(collected_at) as as_of_date
FROM sofia.security_observations
WHERE source = 'GDELT'
  AND event_time_start >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY country_code, country_name;

CREATE INDEX idx_mv_gdelt_country_code ON sofia.mv_security_country_gdelt(country_code);
CREATE INDEX idx_mv_gdelt_severity ON sofia.mv_security_country_gdelt(severity_norm DESC);

-- ============================================================================
-- 3. STRUCTURAL RISK SUMMARY (World Bank)
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_structural CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_country_structural AS
WITH latest_indicators AS (
    SELECT
        country_code,
        country_name,
        raw_payload->>'indicator_name' as indicator_name,
        severity_norm,
        ROW_NUMBER() OVER (
            PARTITION BY country_code, raw_payload->>'indicator_code'
            ORDER BY event_time_start DESC
        ) as rn
    FROM sofia.security_observations
    WHERE source = 'WORLD_BANK'
      AND signal_type = 'structural'
)
SELECT
    country_code,
    country_name,
    AVG(severity_norm) as structural_risk_score,
    COUNT(DISTINCT indicator_name) as indicators_count,
    'WORLD_BANK' as data_source,
    CURRENT_TIMESTAMP as as_of_date
FROM latest_indicators
WHERE rn = 1
GROUP BY country_code, country_name;

CREATE INDEX idx_mv_structural_country_code ON sofia.mv_security_country_structural(country_code);
CREATE INDEX idx_mv_structural_risk ON sofia.mv_security_country_structural(structural_risk_score DESC);

-- ============================================================================
-- 4. COMBINED HYBRID SUMMARY
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_combined CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_country_combined AS
WITH acute_risk AS (
    SELECT
        COALESCE(a.country_code, g.country_code) as country_code,
        COALESCE(a.country_name, g.country_name) as country_name,
        GREATEST(
            COALESCE(a.severity_norm, 0),
            COALESCE(g.severity_norm, 0)
        ) as acute_risk_score,
        COALESCE(a.incidents, 0) + COALESCE(g.incidents, 0) as total_incidents,
        COALESCE(a.fatalities, 0) as fatalities
    FROM sofia.mv_security_country_acled a
    FULL OUTER JOIN sofia.mv_security_country_gdelt g
        ON a.country_code = g.country_code
)
SELECT
    COALESCE(ar.country_code, sr.country_code) as country_code,
    COALESCE(ar.country_name, sr.country_name) as country_name,
    ar.acute_risk_score,
    sr.structural_risk_score,
    -- Hybrid Score: 65% acute + 35% structural
    (COALESCE(ar.acute_risk_score, 0) * 0.65 + COALESCE(sr.structural_risk_score, 0) * 0.35) as total_risk_score,
    ar.total_incidents,
    ar.fatalities,
    sr.indicators_count,
    CASE
        WHEN (COALESCE(ar.acute_risk_score, 0) * 0.65 + COALESCE(sr.structural_risk_score, 0) * 0.35) >= 80 THEN 'Critical'
        WHEN (COALESCE(ar.acute_risk_score, 0) * 0.65 + COALESCE(sr.structural_risk_score, 0) * 0.35) >= 60 THEN 'High'
        WHEN (COALESCE(ar.acute_risk_score, 0) * 0.65 + COALESCE(sr.structural_risk_score, 0) * 0.35) >= 40 THEN 'Elevated'
        WHEN (COALESCE(ar.acute_risk_score, 0) * 0.65 + COALESCE(sr.structural_risk_score, 0) * 0.35) >= 20 THEN 'Moderate'
        ELSE 'Low'
    END as risk_level,
    CURRENT_TIMESTAMP as as_of_date
FROM acute_risk ar
FULL OUTER JOIN sofia.mv_security_country_structural sr
    ON ar.country_code = sr.country_code;

CREATE INDEX idx_mv_combined_country_code ON sofia.mv_security_country_combined(country_code);
CREATE INDEX idx_mv_combined_total_risk ON sofia.mv_security_country_combined(total_risk_score DESC);
CREATE INDEX idx_mv_combined_risk_level ON sofia.mv_security_country_combined(risk_level);

-- ============================================================================
-- 5. REFRESH FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.refresh_security_hybrid_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_acled;
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_gdelt;
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_structural;
    REFRESH MATERIALIZED VIEW sofia.mv_security_country_combined;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. COMMENTS
-- ============================================================================

COMMENT ON MATERIALIZED VIEW sofia.mv_security_country_acled IS 'ACLED acute security events by country (90-day window)';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_country_gdelt IS 'GDELT momentum signals by country (90-day window)';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_country_structural IS 'World Bank structural risk indicators by country';
COMMENT ON MATERIALIZED VIEW sofia.mv_security_country_combined IS 'Hybrid security risk combining acute (65%) and structural (35%) scores';
COMMENT ON FUNCTION sofia.refresh_security_hybrid_views() IS 'Refresh all security hybrid model views';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
