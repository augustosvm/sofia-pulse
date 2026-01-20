-- ============================================================================
-- Migration 010: Security Intelligence Enterprise Upgrade
-- Purpose: Add stress_index, spillover_risk, deterministic narrative support
-- ============================================================================
-- Dependencies: 005_security_map_views.sql must be applied first
-- Note: This ADDS columns to existing view, does NOT replace core logic
-- ============================================================================

-- Upgrade the combined view with enterprise metrics
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_country_combined CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_security_country_combined AS
WITH event_stats AS (
    SELECT 
        country_code,
        country_name,
        -- Event counts by period for stress calculation
        COUNT(*) FILTER (WHERE event_time_start >= CURRENT_DATE - INTERVAL '30 days') as events_30d,
        COUNT(*) FILTER (WHERE event_time_start >= CURRENT_DATE - INTERVAL '90 days') as events_90d,
        COUNT(*) FILTER (WHERE event_time_start >= CURRENT_DATE - INTERVAL '180 days') as events_180d,
        COUNT(*) as total_incidents,
        COALESCE(SUM(fatalities), 0) as fatalities,
        -- Severity weighted score
        AVG(severity_norm) as avg_severity,
        MAX(event_time_start) as last_event_date,
        -- Sources transparency
        ARRAY_AGG(DISTINCT source ORDER BY source) as sources_used,
        MAX(coverage_score_global) as coverage_score_global
    FROM sofia.security_observations
    WHERE event_time_start >= CURRENT_DATE - INTERVAL '365 days'
      AND coverage_scope = 'global_comparable'
      AND country_code IS NOT NULL
    GROUP BY country_code, country_name
),
acute_calculation AS (
    SELECT 
        es.*,
        -- Acute Risk: Normalized severity * recency weight
        LEAST(100, GREATEST(0,
            COALESCE(es.avg_severity, 0) * 
            CASE 
                WHEN es.events_30d > 100 THEN 1.5
                WHEN es.events_30d > 50 THEN 1.2
                WHEN es.events_30d > 10 THEN 1.0
                ELSE 0.8
            END
        )) as acute_risk_score,
        
        -- Stress Index: Are things escalating?
        CASE 
            WHEN es.events_90d = 0 THEN 0
            ELSE ROUND(
                (es.events_30d::numeric / NULLIF(es.events_90d / 3.0, 0)) * 100 - 100
            , 2)
        END as stress_index  -- Positive = escalating, Negative = de-escalating
        
    FROM event_stats es
),
final_calculation AS (
    SELECT 
        ac.country_code,
        ac.country_name,
        ac.acute_risk_score,
        -- Structural risk placeholder (would come from World Bank/governance data)
        0::numeric as structural_risk_score,
        -- Total risk (weighted blend)
        ROUND((ac.acute_risk_score * 0.65 + 0 * 0.35), 2) as total_risk_score,
        -- Risk level classification
        CASE 
            WHEN ac.acute_risk_score >= 80 THEN 'Critical'
            WHEN ac.acute_risk_score >= 60 THEN 'High'
            WHEN ac.acute_risk_score >= 40 THEN 'Elevated'
            WHEN ac.acute_risk_score >= 20 THEN 'Moderate'
            ELSE 'Low'
        END as risk_level,
        ac.total_incidents,
        ac.fatalities,
        ac.events_30d,
        ac.events_90d,
        ac.events_180d,
        ac.stress_index,
        -- Indicators count (placeholder for structural)
        0 as indicators_count,
        ac.coverage_score_global,
        ac.sources_used,
        -- Confidence score (0-1)
        LEAST(1.0, GREATEST(0.0,
            0.4 * LEAST(1.0, ac.total_incidents::numeric / 500) +
            0.3 * COALESCE(ac.coverage_score_global, 0) / 100.0 +
            0.3 * CASE WHEN ac.last_event_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1.0
                       WHEN ac.last_event_date >= CURRENT_DATE - INTERVAL '30 days' THEN 0.8
                       ELSE 0.5 END
        ))::numeric(3,2) as confidence_score,
        ac.last_event_date as as_of_date,
        NOW() as updated_at
    FROM acute_calculation ac
)
SELECT * FROM final_calculation
ORDER BY total_risk_score DESC;

-- Unique index for CONCURRENTLY refresh
CREATE UNIQUE INDEX idx_mv_sec_combined_cc ON sofia.mv_security_country_combined(country_code);
CREATE INDEX idx_mv_sec_combined_risk ON sofia.mv_security_country_combined(risk_level);

-- ============================================================================
-- Spillover Risk View (requires borders/neighbors data)
-- For now, scaffold with NULL spillover - can be populated when borders exist
-- ============================================================================
CREATE OR REPLACE VIEW sofia.v_security_spillover AS
SELECT 
    c.country_code,
    c.total_risk_score as own_risk,
    -- Spillover would be: AVG(neighbors.total_risk_score) * 0.3 + own_risk * 0.7
    -- Without borders table, we return own_risk as spillover
    c.total_risk_score as spillover_risk,
    NULL::text[] as neighbor_codes
FROM sofia.mv_security_country_combined c;

-- ============================================================================
-- Refresh Instructions:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_country_combined;
-- ============================================================================
