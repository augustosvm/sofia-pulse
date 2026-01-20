-- FIX: Recreate ACLED view to include ALL ACLED data (not just 90 days)
-- This is needed because LATAM data has incorrect event_time_start

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
  AND country_code IS NOT NULL
  -- REMOVED: AND event_time_start >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY country_code, country_name;

CREATE INDEX idx_mv_acled_country_code ON sofia.mv_security_country_acled(country_code);
CREATE INDEX idx_mv_acled_severity ON sofia.mv_security_country_acled(severity_norm DESC);

-- Refresh combined view
REFRESH MATERIALIZED VIEW sofia.mv_security_country_gdelt;
REFRESH MATERIALIZED VIEW sofia.mv_security_country_structural;
REFRESH MATERIALIZED VIEW sofia.mv_security_country_combined;
