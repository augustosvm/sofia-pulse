-- ============================================================================
-- Migration 017: Women Intelligence and NGO Coverage Domains
-- Purpose: Add 2 new enterprise intelligence domains using existing data
-- Depends on: countries table, acled_aggregated, organizations
-- ============================================================================

-- ============================================================================
-- DATA SOURCE NOTES (from schema inventory):
-- 
-- WOMEN INTELLIGENCE:
--   - Base: sofia.acled_aggregated (aggregated by week, has country_id)
--   - Columns: week, events (count), fatalities, event_type, country_id
--   - Geo: JOIN countries ON country_id = countries.id to get iso_alpha2
--   - NO MAPPING TABLE NEEDED (direct join)
--
-- NGO COVERAGE:
--   - Uses sofia.industry_signals with category filter for NGO/humanitarian
--   - Geo: Requires signal_country_map (already exists)
-- ============================================================================

-- ============================================================================
-- 1. WOMEN INTELLIGENCE MV (using ACLED aggregated data)
-- Violence incidents by country - no mapping table needed
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_women_intelligence_by_country;

CREATE MATERIALIZED VIEW sofia.mv_women_intelligence_by_country AS
WITH violence_stats AS (
    SELECT 
        c.iso_alpha2 AS country_code,
        SUM(a.events) FILTER (WHERE a.week >= CURRENT_DATE - INTERVAL '30 days') AS events_30d,
        SUM(a.events) FILTER (WHERE a.week >= CURRENT_DATE - INTERVAL '90 days') AS events_90d,
        SUM(a.fatalities) FILTER (WHERE a.week >= CURRENT_DATE - INTERVAL '90 days') AS fatalities_90d,
        COUNT(DISTINCT a.event_type) AS event_type_diversity
    FROM sofia.acled_aggregated a
    JOIN sofia.countries c ON a.country_id = c.id
    WHERE c.iso_alpha2 IS NOT NULL
      AND a.week >= CURRENT_DATE - INTERVAL '180 days'
    GROUP BY c.iso_alpha2
)
SELECT 
    c.iso_alpha2 AS country_code,
    COALESCE(vs.events_30d, 0) AS events_30d,
    COALESCE(vs.events_90d, 0) AS events_90d,
    COALESCE(vs.fatalities_90d, 0) AS fatalities_90d,
    0 AS women_specific_events, -- Not available in aggregated data
    COALESCE(vs.event_type_diversity, 0) AS event_type_diversity,
    -- Momentum
    CASE 
        WHEN COALESCE(vs.events_90d, 0) > 0 
        THEN ROUND((COALESCE(vs.events_30d, 0)::numeric / NULLIF(COALESCE(vs.events_90d, 0) / 3.0, 0)), 2)
        ELSE 0
    END AS violence_momentum,
    -- Risk score (0-100)
    LEAST(100, ROUND(
        (COALESCE(vs.events_30d, 0) * 2 + 
         COALESCE(vs.fatalities_90d, 0) * 0.5)::numeric / 10
    , 0)) AS women_risk_score,
    -- Tier
    CASE 
        WHEN COALESCE(vs.events_30d, 0) >= 500 THEN 'women_crisis'
        WHEN COALESCE(vs.events_30d, 0) >= 100 THEN 'women_high_risk'
        WHEN COALESCE(vs.events_30d, 0) >= 20 THEN 'women_watch'
        WHEN COALESCE(vs.events_30d, 0) > 0 THEN 'women_low_risk'
        ELSE 'no_data'
    END AS women_tier,
    -- Confidence (high because ACLED is reliable source)
    CASE
        WHEN COALESCE(vs.events_90d, 0) = 0 THEN 0.0
        ELSE LEAST(0.95, GREATEST(0.3,
            0.5 * LEAST(1.0, COALESCE(vs.events_90d, 0)::numeric / 200) +
            0.3 * LEAST(1.0, COALESCE(vs.event_type_diversity, 0)::numeric / 5) +
            0.2
        ))
    END::numeric(3,2) AS confidence,
    CURRENT_DATE - INTERVAL '1 day' AS as_of_date,
    NOW() AS updated_at
FROM sofia.countries c
LEFT JOIN violence_stats vs ON c.iso_alpha2 = vs.country_code
WHERE c.iso_alpha2 IS NOT NULL;

CREATE UNIQUE INDEX idx_mv_women_intelligence_cc ON sofia.mv_women_intelligence_by_country(country_code);

-- ============================================================================
-- 2. NGO COVERAGE MV (using industry_signals via existing signal_country_map)
-- Filters signals for NGO/humanitarian/civil-society categories
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_ngo_coverage_by_country;

CREATE MATERIALIZED VIEW sofia.mv_ngo_coverage_by_country AS
WITH ngo_signals AS (
    SELECT 
        m.country_code,
        s.published_at,
        s.category,
        m.confidence_hint
    FROM sofia.industry_signals s
    JOIN sofia.signal_country_map m ON s.id = m.signal_id
    WHERE s.published_at >= CURRENT_DATE - INTERVAL '180 days'
      AND (
          s.category ILIKE '%ngo%'
          OR s.category ILIKE '%humanitarian%'
          OR s.category ILIKE '%civil%society%'
          OR s.category ILIKE '%nonprofit%'
          OR s.category ILIKE '%charity%'
          OR s.category ILIKE '%foundation%'
          OR s.title ILIKE '%ngo%'
          OR s.title ILIKE '%humanitarian%'
      )
),
ngo_stats AS (
    SELECT 
        country_code,
        COUNT(*) AS ngo_signals_total,
        COUNT(*) FILTER (WHERE published_at >= CURRENT_DATE - INTERVAL '30 days') AS ngo_signals_30d,
        COUNT(*) FILTER (WHERE published_at >= CURRENT_DATE - INTERVAL '90 days') AS ngo_signals_90d,
        COUNT(DISTINCT category) AS sector_diversity,
        AVG(confidence_hint) AS avg_confidence
    FROM ngo_signals
    GROUP BY country_code
)
SELECT 
    c.iso_alpha2 AS country_code,
    COALESCE(ns.ngo_signals_total, 0) AS ngo_signals_total,
    COALESCE(ns.ngo_signals_30d, 0) AS ngo_signals_30d,
    COALESCE(ns.ngo_signals_90d, 0) AS ngo_signals_90d,
    COALESCE(ns.sector_diversity, 0) AS sector_diversity,
    -- Momentum
    CASE 
        WHEN COALESCE(ns.ngo_signals_90d, 0) > 0 
        THEN ROUND((COALESCE(ns.ngo_signals_30d, 0)::numeric / NULLIF(COALESCE(ns.ngo_signals_90d, 0) / 3.0, 0)), 2)
        ELSE 0
    END AS ngo_momentum,
    -- Coverage score (0-100)
    LEAST(100, ROUND(
        (COALESCE(ns.ngo_signals_30d, 0) * 3 + 
         COALESCE(ns.sector_diversity, 0) * 10)::numeric
    , 0)) AS ngo_coverage_score,
    -- Tier
    CASE 
        WHEN COALESCE(ns.ngo_signals_30d, 0) >= 50 THEN 'ngo_dense'
        WHEN COALESCE(ns.ngo_signals_30d, 0) >= 20 THEN 'ngo_active'
        WHEN COALESCE(ns.ngo_signals_30d, 0) >= 5 THEN 'ngo_emerging'
        WHEN COALESCE(ns.ngo_signals_30d, 0) > 0 THEN 'ngo_sparse'
        ELSE 'no_data'
    END AS ngo_tier,
    -- Confidence (capped due to signal-based inference)
    CASE
        WHEN COALESCE(ns.ngo_signals_90d, 0) = 0 THEN 0.0
        ELSE LEAST(0.80, GREATEST(0.3,
            0.4 * LEAST(1.0, COALESCE(ns.ngo_signals_90d, 0)::numeric / 100) +
            0.3 * LEAST(1.0, COALESCE(ns.sector_diversity, 0)::numeric / 5) +
            0.3 * COALESCE(ns.avg_confidence, 0.5)
        ))
    END::numeric(3,2) AS confidence,
    CURRENT_DATE - INTERVAL '1 day' AS as_of_date,
    NOW() AS updated_at
FROM sofia.countries c
LEFT JOIN ngo_stats ns ON c.iso_alpha2 = ns.country_code
WHERE c.iso_alpha2 IS NOT NULL;

CREATE UNIQUE INDEX idx_mv_ngo_coverage_cc ON sofia.mv_ngo_coverage_by_country(country_code);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON MATERIALIZED VIEW sofia.mv_women_intelligence_by_country IS 
'Women/GBV risk intelligence by country. Source: ACLED aggregated violence data. Direct join, no mapping table.';

COMMENT ON MATERIALIZED VIEW sofia.mv_ngo_coverage_by_country IS 
'NGO/Civil society coverage by country. Source: industry_signals filtered for NGO categories via signal_country_map.';
