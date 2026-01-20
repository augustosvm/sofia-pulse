-- ============================================================================
-- Migration 016: Performance-Optimized Intelligence MVs
-- Purpose: Use mapping tables only (no text joins in MVs)
-- Depends on: Migration 015 + backfills
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1) INDUSTRY SIGNALS HEAT
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_industry_signals_heat_by_country;

CREATE MATERIALIZED VIEW sofia.mv_industry_signals_heat_by_country AS
WITH mapped_signals AS (
    SELECT
        m.country_code,
        s.published_at,
        COALESCE(s.category, 'General') AS category,
        m.confidence_hint
    FROM sofia.industry_signals s
    JOIN sofia.signal_country_map m ON s.id = m.signal_id
    WHERE s.published_at >= CURRENT_DATE - INTERVAL '180 days'
),
signal_stats AS (
    SELECT
        ms.country_code,
        COUNT(*) FILTER (WHERE ms.published_at >= CURRENT_DATE - INTERVAL '30 days') AS signals_30d,
        COUNT(*) FILTER (WHERE ms.published_at >= CURRENT_DATE - INTERVAL '90 days') AS signals_90d,
        COUNT(DISTINCT ms.category) AS sector_diversity,
        MODE() WITHIN GROUP (ORDER BY ms.category) AS dominant_sector,
        AVG(ms.confidence_hint) AS avg_confidence
    FROM mapped_signals ms
    GROUP BY ms.country_code
)
SELECT
    c.iso_alpha2 AS country_code,
    signals_30d,
    signals_90d,
    sector_diversity,
    dominant_sector,
    CASE
        WHEN signals_90d > 0 THEN ROUND((signals_30d::numeric / NULLIF(signals_90d / 3.0, 0)), 2)
        ELSE 0
    END AS signal_momentum,
    LEAST(100, ROUND((signals_30d * 2 + signals_90d * 0.5 + sector_diversity * 10)::numeric / 5, 0)) AS heat_score,
    CASE
        WHEN signals_30d >= 100 THEN 'signals_hot'
        WHEN signals_30d >= 50 THEN 'signals_active'
        WHEN signals_30d >= 10 THEN 'signals_emerging'
        ELSE 'signals_quiet'
    END AS heat_tier,
    LEAST(1.0, GREATEST(0.0,
        0.4 * LEAST(1.0, signals_90d::numeric / 500) +
        0.3 * LEAST(1.0, sector_diversity::numeric / 5) +
        0.3 * COALESCE(avg_confidence, 0.5)
    ))::numeric(3,2) AS confidence,
    CURRENT_DATE - INTERVAL '1 day' AS as_of_date,
    NOW() AS updated_at
FROM signal_stats ss
JOIN sofia.countries c ON c.iso_alpha2 = ss.country_code;

CREATE UNIQUE INDEX idx_mv_signals_heat_cc ON sofia.mv_industry_signals_heat_by_country(country_code);

-- ----------------------------------------------------------------------------
-- 2) CYBER RISK DENSITY
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_cyber_risk_by_country;

CREATE MATERIALIZED VIEW sofia.mv_cyber_risk_by_country AS
WITH mapped_events AS (
    SELECT
        m.country_code,
        e.published_date,
        e.severity,
        m.confidence_hint
    FROM sofia.cybersecurity_events e
    JOIN sofia.cyber_event_country_map m ON e.id = m.event_id
    WHERE e.published_date >= CURRENT_DATE - INTERVAL '180 days'
),
cyber_stats AS (
    SELECT
        me.country_code,
        COUNT(*) FILTER (WHERE me.published_date >= CURRENT_DATE - INTERVAL '90 days') AS events_90d,
        COUNT(*) FILTER (WHERE me.severity ILIKE '%critical%') AS critical_events,
        AVG(CASE
            WHEN me.severity ILIKE '%critical%' THEN 10
            WHEN me.severity ILIKE '%high%' THEN 7
            WHEN me.severity ILIKE '%medium%' THEN 4
            ELSE 1
        END) AS severity_avg,
        AVG(me.confidence_hint) AS avg_confidence
    FROM mapped_events me
    GROUP BY me.country_code
)
SELECT
    c.iso_alpha2 AS country_code,
    events_90d,
    critical_events,
    ROUND(COALESCE(severity_avg, 1), 2) AS severity_avg,
    LEAST(100, ROUND((events_90d * COALESCE(severity_avg, 1) / 5)::numeric, 0)) AS cyber_risk_score,
    CASE
        WHEN events_90d * COALESCE(severity_avg, 1) >= 50 THEN 'cyber_critical'
        WHEN events_90d * COALESCE(severity_avg, 1) >= 20 THEN 'cyber_high'
        WHEN events_90d * COALESCE(severity_avg, 1) >= 5 THEN 'cyber_moderate'
        ELSE 'cyber_low'
    END AS cyber_tier,
    LEAST(0.85, GREATEST(0.0,
        0.5 * LEAST(1.0, events_90d::numeric / 50) +
        0.2 * CASE WHEN critical_events > 0 THEN 1 ELSE 0.5 END +
        0.3 * COALESCE(avg_confidence, 0.5)
    ))::numeric(3,2) AS confidence,
    CURRENT_DATE - INTERVAL '1 day' AS as_of_date,
    NOW() AS updated_at
FROM cyber_stats cs
JOIN sofia.countries c ON c.iso_alpha2 = cs.country_code;

CREATE UNIQUE INDEX idx_mv_cyber_risk_cc ON sofia.mv_cyber_risk_by_country(country_code);

-- ----------------------------------------------------------------------------
-- 3) CLINICAL TRIALS ACTIVITY
-- ----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_clinical_trials_by_country;

CREATE MATERIALIZED VIEW sofia.mv_clinical_trials_by_country AS
WITH mapped_trials AS (
    SELECT
        m.country_code,
        t.start_date,
        t.phase,
        COALESCE(t.condition, 'Unknown') AS condition,
        m.confidence_hint
    FROM sofia.clinical_trials t
    JOIN sofia.trial_country_map m ON t.nct_id = m.nct_id
),
trial_stats AS (
    SELECT
        mt.country_code,
        COUNT(*) AS trials_total,
        COUNT(*) FILTER (WHERE mt.start_date >= CURRENT_DATE - INTERVAL '12 months') AS trials_12m,
        COUNT(*) FILTER (WHERE mt.phase ILIKE '%3%' OR mt.phase ILIKE '%iii%') AS phase3_count,
        COUNT(DISTINCT mt.condition) AS area_diversity,
        AVG(mt.confidence_hint) AS avg_confidence
    FROM mapped_trials mt
    GROUP BY mt.country_code
)
SELECT
    c.iso_alpha2 AS country_code,
    trials_total,
    trials_12m,
    phase3_count,
    area_diversity,
    LEAST(100, ROUND((trials_12m * 3 + phase3_count * 5 + area_diversity * 2)::numeric, 0)) AS trial_activity_score,
    CASE
        WHEN trials_12m >= 20 THEN 'pharma_hub'
        WHEN trials_12m >= 10 THEN 'pharma_active'
        WHEN trials_12m >= 3 THEN 'pharma_emerging'
        ELSE 'pharma_nascent'
    END AS pharma_tier,
    LEAST(1.0, GREATEST(0.0,
        0.4 * LEAST(1.0, trials_12m::numeric / 30) +
        0.3 * LEAST(1.0, phase3_count::numeric / 10) +
        0.3 * COALESCE(avg_confidence, 0.7)
    ))::numeric(3,2) AS confidence,
    CURRENT_DATE - INTERVAL '1 day' AS as_of_date,
    NOW() AS updated_at
FROM trial_stats ts
JOIN sofia.countries c ON c.iso_alpha2 = ts.country_code;

CREATE UNIQUE INDEX idx_mv_trials_cc ON sofia.mv_clinical_trials_by_country(country_code);

-- ----------------------------------------------------------------------------
-- REFRESH COMMANDS (run after backfill scripts)
-- ----------------------------------------------------------------------------
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_industry_signals_heat_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_cyber_risk_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_clinical_trials_by_country;
