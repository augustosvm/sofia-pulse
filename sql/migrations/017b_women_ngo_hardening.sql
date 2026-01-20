-- ============================================================================
-- Migration 017b: Women & NGO Enterprise Hardening
-- Purpose: Fix semantics (Women=proxy), add NGO keyword rules, fix time windows
-- SAFETY: This migration is idempotent. ngo_keyword_rules preserves manual tuning.
-- MVs: DROP/CREATE is intentional; requires REFRESH afterwards. Validate grants.
-- ============================================================================

-- ============================================================================
-- TASK A: NGO KEYWORD RULES TABLE (enterprise deterministic filter)
-- SAFETY: CREATE IF NOT EXISTS preserves existing keyword tuning
-- ============================================================================

-- DO NOT DROP: CREATE TABLE IF NOT EXISTS preserves manual tuning
CREATE TABLE IF NOT EXISTS sofia.ngo_keyword_rules (
    keyword TEXT PRIMARY KEY,
    field TEXT NOT NULL DEFAULT 'both',  -- category, title, both
    weight INT NOT NULL DEFAULT 1
);

-- Seed default keywords (will not overwrite existing due to ON CONFLICT)
INSERT INTO sofia.ngo_keyword_rules (keyword, field, weight) VALUES
    ('ngo', 'both', 2),
    ('humanitarian', 'both', 2),
    ('civil society', 'both', 2),
    ('nonprofit', 'both', 1),
    ('non-profit', 'both', 1),
    ('charity', 'both', 1),
    ('foundation', 'category', 1),
    ('relief', 'title', 1),
    ('aid organization', 'both', 2),
    ('development agency', 'both', 1)
ON CONFLICT DO NOTHING;

-- Idempotent index creation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'sofia' AND indexname = 'idx_ngo_keywords') THEN
        CREATE INDEX idx_ngo_keywords ON sofia.ngo_keyword_rules(keyword);
    END IF;
END $$;

COMMENT ON TABLE sofia.ngo_keyword_rules IS 'Enterprise rule table for deterministic NGO signal classification. Preserves manual tuning.';


-- ============================================================================
-- TASK B: WOMEN INTELLIGENCE MV (enterprise honest proxy)
-- Fixed: week-based boundaries, proxy flag, NULL for unavailable fields
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_women_intelligence_by_country;

CREATE MATERIALIZED VIEW sofia.mv_women_intelligence_by_country AS
WITH violence_stats AS (
    SELECT 
        c.iso_alpha2 AS country_code,
        SUM(a.events) FILTER (WHERE a.week >= date_trunc('week', CURRENT_DATE) - interval '4 weeks') AS events_30d,
        SUM(a.events) FILTER (WHERE a.week >= date_trunc('week', CURRENT_DATE) - interval '13 weeks') AS events_90d,
        SUM(a.fatalities) FILTER (WHERE a.week >= date_trunc('week', CURRENT_DATE) - interval '13 weeks') AS fatalities_90d,
        COUNT(DISTINCT a.event_type) AS event_type_diversity
    FROM sofia.acled_aggregated a
    JOIN sofia.countries c ON a.country_id = c.id
    WHERE c.iso_alpha2 IS NOT NULL
      AND a.week >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
    GROUP BY c.iso_alpha2
)
SELECT 
    c.iso_alpha2 AS country_code,
    COALESCE(vs.events_30d, 0) AS events_30d,
    COALESCE(vs.events_90d, 0) AS events_90d,
    COALESCE(vs.fatalities_90d, 0) AS fatalities_90d,
    NULL::integer AS women_specific_events, -- NOT AVAILABLE in ACLED aggregated
    COALESCE(vs.event_type_diversity, 0) AS event_type_diversity,
    -- Data scope: enterprise honest proxy flag
    'proxy_general_violence'::text AS data_scope,
    -- Momentum (week-aligned)
    CASE 
        WHEN COALESCE(vs.events_90d, 0) > 0 
        THEN ROUND((COALESCE(vs.events_30d, 0)::numeric / NULLIF(COALESCE(vs.events_90d, 0) / 3.0, 0)), 2)
        ELSE 0
    END AS violence_momentum,
    -- Risk score (0-100)
    LEAST(100, ROUND(
        (COALESCE(vs.events_30d, 0) * 2 + 
         COALESCE(vs.fatalities_90d, 0) * 0.5)::numeric / 10
    , 0)) AS violence_risk_score,
    -- Tier
    CASE 
        WHEN COALESCE(vs.events_30d, 0) >= 500 THEN 'violence_crisis'
        WHEN COALESCE(vs.events_30d, 0) >= 100 THEN 'violence_high'
        WHEN COALESCE(vs.events_30d, 0) >= 20 THEN 'violence_watch'
        WHEN COALESCE(vs.events_30d, 0) > 0 THEN 'violence_low'
        ELSE 'no_data'
    END AS violence_tier,
    -- Confidence
    CASE
        WHEN COALESCE(vs.events_90d, 0) = 0 THEN 0.0
        ELSE LEAST(0.90, GREATEST(0.3,
            0.5 * LEAST(1.0, COALESCE(vs.events_90d, 0)::numeric / 200) +
            0.3 * LEAST(1.0, COALESCE(vs.event_type_diversity, 0)::numeric / 5) +
            0.1
        ))
    END::numeric(3,2) AS confidence,
    CURRENT_DATE - INTERVAL '1 day' AS as_of_date,
    NOW() AS updated_at
FROM sofia.countries c
LEFT JOIN violence_stats vs ON c.iso_alpha2 = vs.country_code
WHERE c.iso_alpha2 IS NOT NULL;

-- Idempotent index creation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'sofia' AND indexname = 'idx_mv_women_intelligence_cc') THEN
        CREATE UNIQUE INDEX idx_mv_women_intelligence_cc ON sofia.mv_women_intelligence_by_country(country_code);
    END IF;
END $$;

COMMENT ON MATERIALIZED VIEW sofia.mv_women_intelligence_by_country IS 
'Violence risk proxy (ACLED). data_scope=proxy_general_violence. No gender-specific data available in source.';

-- ============================================================================
-- TASK C: NGO COVERAGE MV (using keyword rules table)
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_ngo_coverage_by_country;

CREATE MATERIALIZED VIEW sofia.mv_ngo_coverage_by_country AS
WITH normalized_signals AS (
    SELECT 
        s.id,
        m.country_code,
        s.published_at,
        lower(COALESCE(s.category, '')) AS category_lower,
        lower(COALESCE(s.title, '')) AS title_lower,
        m.confidence_hint
    FROM sofia.industry_signals s
    JOIN sofia.signal_country_map m ON s.id = m.signal_id
    WHERE s.published_at >= date_trunc('week', CURRENT_DATE) - interval '26 weeks'
),
ngo_matched AS (
    SELECT DISTINCT ON (ns.id)
        ns.country_code,
        ns.published_at,
        ns.category_lower,
        ns.confidence_hint
    FROM normalized_signals ns
    WHERE EXISTS (
        SELECT 1 FROM sofia.ngo_keyword_rules r
        WHERE (r.field = 'both' OR r.field = 'category') 
          AND ns.category_lower LIKE '%' || r.keyword || '%'
    )
    OR EXISTS (
        SELECT 1 FROM sofia.ngo_keyword_rules r
        WHERE (r.field = 'both' OR r.field = 'title') 
          AND ns.title_lower LIKE '%' || r.keyword || '%'
    )
    ORDER BY ns.id, ns.published_at DESC, ns.confidence_hint DESC
),
ngo_stats AS (
    SELECT 
        country_code,
        COUNT(*) AS ngo_signals_total,
        COUNT(*) FILTER (WHERE published_at >= date_trunc('week', CURRENT_DATE) - interval '4 weeks') AS ngo_signals_30d,
        COUNT(*) FILTER (WHERE published_at >= date_trunc('week', CURRENT_DATE) - interval '13 weeks') AS ngo_signals_90d,
        COUNT(DISTINCT category_lower) AS sector_diversity,
        AVG(confidence_hint) AS avg_confidence
    FROM ngo_matched
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
    -- Confidence
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

-- Idempotent index creation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'sofia' AND indexname = 'idx_mv_ngo_coverage_cc') THEN
        CREATE UNIQUE INDEX idx_mv_ngo_coverage_cc ON sofia.mv_ngo_coverage_by_country(country_code);
    END IF;
END $$;

COMMENT ON MATERIALIZED VIEW sofia.mv_ngo_coverage_by_country IS 
'NGO/Civil society coverage by country. Uses sofia.ngo_keyword_rules for deterministic classification.';

