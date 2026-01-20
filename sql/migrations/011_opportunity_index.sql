-- ============================================================================
-- Migration 011: Opportunity Composite Index
-- Purpose: Create Global Opportunity Index combining Capital, Talent, Security
-- Formula: opportunity = normalize(capital) + normalize(talent) - normalize(risk)
-- ============================================================================
-- Dependencies: 008, 009, 010 must be applied first
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_opportunity_by_country CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_opportunity_by_country AS
WITH capital_norm AS (
    SELECT 
        country_code,
        total_vol_12m,
        momentum_pct,
        confidence_score as capital_confidence,
        -- Normalize to 0-100 scale
        CASE 
            WHEN total_vol_12m >= 10000000000 THEN 100  -- $10B+
            WHEN total_vol_12m >= 1000000000 THEN 80   -- $1B+
            WHEN total_vol_12m >= 100000000 THEN 60    -- $100M+
            WHEN total_vol_12m >= 10000000 THEN 40     -- $10M+
            ELSE 20
        END as capital_score
    FROM sofia.mv_capital_analytics
),
talent_norm AS (
    SELECT 
        country_code,
        avg_gap_score,
        total_jobs,
        total_papers,
        confidence,
        -- Talent score: Low gap = good, many jobs = good
        CASE 
            WHEN overall_gap_type = 'aligned' THEN 80
            WHEN overall_gap_type = 'market_hungry' THEN 60  -- Demand exists
            WHEN overall_gap_type = 'moderate_gap' THEN 50
            ELSE 30  -- academia_ahead = less immediate opportunity
        END + 
        LEAST(20, total_jobs::numeric / 100) as talent_score  -- Bonus for job volume
    FROM sofia.mv_skill_gap_country_summary
),
security_norm AS (
    SELECT 
        country_code,
        total_risk_score,
        risk_level,
        confidence_score as security_confidence,
        -- Inverted: Low risk = high score
        GREATEST(0, 100 - total_risk_score) as security_score
    FROM sofia.mv_security_country_combined
),
all_countries AS (
    SELECT country_code FROM capital_norm
    UNION SELECT country_code FROM talent_norm
    UNION SELECT country_code FROM security_norm
),
combined AS (
    SELECT 
        ac.country_code,
        -- Capital Component
        COALESCE(c.capital_score, 0) as capital_score,
        COALESCE(c.total_vol_12m, 0) as capital_volume,
        COALESCE(c.momentum_pct, 0) as capital_momentum,
        COALESCE(c.capital_confidence, 0) as capital_confidence,
        -- Talent Component
        COALESCE(t.talent_score, 0) as talent_score,
        COALESCE(t.total_jobs, 0) as talent_jobs,
        COALESCE(t.total_papers, 0) as talent_papers,
        COALESCE(t.confidence, 0) as talent_confidence,
        -- Security Component (inverted)
        COALESCE(s.security_score, 50) as security_score,  -- Default 50 if unknown
        COALESCE(s.total_risk_score, 0) as security_risk,
        s.risk_level as security_level,
        COALESCE(s.security_confidence, 0) as security_confidence
    FROM all_countries ac
    LEFT JOIN capital_norm c ON ac.country_code = c.country_code
    LEFT JOIN talent_norm t ON ac.country_code = t.country_code
    LEFT JOIN security_norm s ON ac.country_code = s.country_code
)
SELECT 
    country_code,
    -- Component scores
    capital_score,
    talent_score,
    security_score,
    -- Composite Opportunity Index (weighted)
    ROUND((
        capital_score * 0.40 +    -- Capital weight 40%
        talent_score * 0.35 +     -- Talent weight 35%
        security_score * 0.25     -- Security weight 25% (inverted)
    ), 2) as opportunity_score,
    -- Tier classification
    CASE 
        WHEN (capital_score * 0.40 + talent_score * 0.35 + security_score * 0.25) >= 80 THEN 'prime_opportunity'
        WHEN (capital_score * 0.40 + talent_score * 0.35 + security_score * 0.25) >= 60 THEN 'high_potential'
        WHEN (capital_score * 0.40 + talent_score * 0.35 + security_score * 0.25) >= 40 THEN 'emerging'
        WHEN (capital_score * 0.40 + talent_score * 0.35 + security_score * 0.25) >= 20 THEN 'developing'
        ELSE 'challenging'
    END as opportunity_tier,
    -- Breakdowns
    capital_volume,
    capital_momentum,
    talent_jobs,
    talent_papers,
    security_risk,
    security_level,
    -- Aggregate confidence
    ROUND((
        COALESCE(capital_confidence, 0) * 0.4 + 
        COALESCE(talent_confidence, 0) * 0.35 + 
        COALESCE(security_confidence, 0) * 0.25
    ), 2)::numeric(3,2) as confidence,
    -- Data coverage flags
    CASE WHEN capital_score > 0 THEN TRUE ELSE FALSE END as has_capital_data,
    CASE WHEN talent_score > 0 THEN TRUE ELSE FALSE END as has_talent_data,
    CASE WHEN security_score != 50 THEN TRUE ELSE FALSE END as has_security_data,
    NOW() as updated_at
FROM combined
ORDER BY opportunity_score DESC;

-- Unique index for CONCURRENTLY refresh
CREATE UNIQUE INDEX idx_mv_opportunity_cc ON sofia.mv_opportunity_by_country(country_code);
CREATE INDEX idx_mv_opportunity_tier ON sofia.mv_opportunity_by_country(opportunity_tier);

-- ============================================================================
-- Refresh Instructions:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_opportunity_by_country;
-- (Must refresh dependencies first: capital, talent, security)
-- ============================================================================
