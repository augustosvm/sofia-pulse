-- ============================================================================
-- Migration 014: Intelligence Expansion Phase 2
-- New Domains: Industry Signals Heat, Cyber Risk, Clinical Trials
-- Fixes: Join strategies for missing country columns
-- ============================================================================

-- ============================================================================
-- 1. INDUSTRY SIGNALS HEAT BY COUNTRY
-- Source: sofia.industry_signals (metadata->>'jurisdiction')
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_industry_signals_heat_by_country;

CREATE MATERIALIZED VIEW sofia.mv_industry_signals_heat_by_country AS
WITH raw_signals AS (
    SELECT 
        -- Try to extract country from metadata jurisdiction, fallback to text match if needed
        UPPER(COALESCE(
            metadata->>'jurisdiction', 
            metadata->>'country_code',
            SUBSTRING(metadata->>'actor1' FROM '\.([a-z]{2})\.'),
            'XX'
        )) as raw_cc,
        published_at as sort_date,
        category
    FROM sofia.industry_signals
),
clean_signals AS (
    SELECT 
        raw_cc as country_code,
        sort_date,
        COALESCE(category, 'General') as category
    FROM raw_signals
    WHERE LENGTH(raw_cc) = 2 AND raw_cc != 'XX'
),
signal_stats AS (
    SELECT 
        country_code,
        COUNT(*) FILTER (WHERE sort_date >= CURRENT_DATE - INTERVAL '30 days') as signals_30d,
        COUNT(*) FILTER (WHERE sort_date >= CURRENT_DATE - INTERVAL '90 days') as signals_90d,
        COUNT(DISTINCT category) as sector_diversity,
        MODE() WITHIN GROUP (ORDER BY category) as dominant_sector
    FROM clean_signals
    WHERE sort_date >= CURRENT_DATE - INTERVAL '180 days'
    GROUP BY country_code
)
SELECT 
    country_code,
    signals_30d,
    signals_90d,
    sector_diversity,
    dominant_sector,
    -- Momentum
    CASE 
        WHEN signals_90d > 0 THEN ROUND((signals_30d::numeric / NULLIF(signals_90d / 3.0, 0)), 2)
        ELSE 0
    END as signal_momentum,
    -- Heat score (0-100)
    LEAST(100, ROUND((signals_30d * 2 + signals_90d * 0.5 + sector_diversity * 10)::numeric / 5, 0)) as heat_score,
    -- Tier
    CASE 
        WHEN signals_30d >= 100 THEN 'signals_hot'
        WHEN signals_30d >= 50 THEN 'signals_active'
        WHEN signals_30d >= 10 THEN 'signals_emerging'
        ELSE 'signals_quiet'
    END as heat_tier,
    -- Confidence
    LEAST(1.0, GREATEST(0.0,
        0.6 * LEAST(1.0, signals_90d::numeric / 500) +
        0.4 * LEAST(1.0, sector_diversity::numeric / 5)
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM signal_stats
ORDER BY heat_score DESC;

CREATE UNIQUE INDEX idx_mv_signals_heat_cc ON sofia.mv_industry_signals_heat_by_country(country_code);


-- ============================================================================
-- 2. CYBER RISK BY COUNTRY
-- Source: sofia.cybersecurity_events (Text extraction from Title/Desc due to missing column)
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_cyber_risk_by_country;

CREATE MATERIALIZED VIEW sofia.mv_cyber_risk_by_country AS
WITH extracted_geo AS (
    SELECT 
        e.id,
        e.severity,
        e.published_date,
        e.title,
        -- Attempt to find country name in title/description (Expensive but necessary)
        c.iso_alpha2 as country_code
    FROM sofia.cybersecurity_events e
    JOIN sofia.countries c ON 
        e.title ILIKE '%' || c.common_name || '%' 
        OR e.description ILIKE '%' || c.common_name || '%'
    WHERE e.published_date >= CURRENT_DATE - INTERVAL '180 days'
),
cyber_stats AS (
    SELECT 
        country_code,
        COUNT(*) FILTER (WHERE published_date >= CURRENT_DATE - INTERVAL '90 days') as events_90d,
        COUNT(*) FILTER (WHERE severity ILIKE '%critical%') as critical_events,
        AVG(CASE 
            WHEN severity ILIKE '%critical%' THEN 10
            WHEN severity ILIKE '%high%' THEN 7
            WHEN severity ILIKE '%medium%' THEN 4
            ELSE 1
        END) as severity_avg
    FROM extracted_geo
    GROUP BY country_code
)
SELECT 
    country_code,
    events_90d,
    critical_events,
    ROUND(COALESCE(severity_avg, 1), 2) as severity_avg,
    -- Risk score (0-100)
    LEAST(100, ROUND((events_90d * COALESCE(severity_avg, 1) / 10)::numeric, 0)) as cyber_risk_score,
    -- Tier
    CASE 
        WHEN events_90d * COALESCE(severity_avg, 1) >= 50 THEN 'cyber_critical' -- Adjusted threshold due to low volume
        WHEN events_90d * COALESCE(severity_avg, 1) >= 20 THEN 'cyber_high'
        WHEN events_90d * COALESCE(severity_avg, 1) >= 5 THEN 'cyber_moderate'
        ELSE 'cyber_low'
    END as cyber_tier,
    -- Confidence (Low due to text matching)
    LEAST(0.8, GREATEST(0.0,
        0.7 * LEAST(1.0, events_90d::numeric / 50) +
        0.3 * CASE WHEN critical_events > 0 THEN 1 ELSE 0.5 END
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM cyber_stats
ORDER BY cyber_risk_score DESC;

CREATE UNIQUE INDEX idx_mv_cyber_risk_cc ON sofia.mv_cyber_risk_by_country(country_code);


-- ============================================================================
-- 3. CLINICAL TRIALS BY COUNTRY
-- Source: sofia.clinical_trials (Join Sponsor -> Organization -> Country)
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_clinical_trials_by_country;

CREATE MATERIALIZED VIEW sofia.mv_clinical_trials_by_country AS
WITH trial_geo AS (
    SELECT 
        t.nct_id,
        t.start_date,
        t.phase,
        t.condition,
        -- Attempt to find country from authors table via institution match
        -- Taking the first match for simplicity in this version
        -- Fallback: Check if sponsor contains country name (e.g. "Merck (China)") 
        -- or location string if we had one.
        (SELECT iso_alpha2 
         FROM sofia.countries 
         WHERE t.sponsor ILIKE '%' || common_name || '%' 
         LIMIT 1
        ) as country_code
    FROM sofia.clinical_trials t
),
trial_stats AS (
    SELECT 
        COALESCE(country_code, 'XX') as country_code,
        COUNT(*) as trials_total,
        COUNT(*) FILTER (WHERE start_date >= CURRENT_DATE - INTERVAL '12 months') as trials_12m,
        COUNT(*) FILTER (WHERE phase ILIKE '%3%' OR phase ILIKE '%iii%') as phase3_count,
        COUNT(DISTINCT condition) as area_diversity
    FROM trial_geo
    GROUP BY country_code
)
SELECT 
    country_code,
    trials_total,
    trials_12m,
    phase3_count,
    area_diversity,
    -- Activity score (0-100)
    LEAST(100, ROUND((trials_12m * 2 + phase3_count * 5 + area_diversity * 3)::numeric, 0)) as trial_activity_score,
    -- Tier
    CASE 
        WHEN trials_12m >= 20 THEN 'pharma_hub' -- Lowered thresholds due to partial matching
        WHEN trials_12m >= 10 THEN 'pharma_active'
        WHEN trials_12m >= 2 THEN 'pharma_emerging'
        ELSE 'pharma_nascent'
    END as pharma_tier,
    -- Confidence
    LEAST(1.0, GREATEST(0.0,
        0.5 * LEAST(1.0, trials_12m::numeric / 50) +
        0.3 * LEAST(1.0, phase3_count::numeric / 10) +
        0.2 * 1.0
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM trial_stats
ORDER BY trial_activity_score DESC;

CREATE UNIQUE INDEX idx_mv_trials_cc ON sofia.mv_clinical_trials_by_country(country_code);
