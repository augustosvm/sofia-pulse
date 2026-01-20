-- ============================================================================
-- Migration 012: New Intelligence Domains Scaffold
-- Purpose: Create empty-but-valid MVs for new domains
-- Domains: Innovation, Brain Drain, Regulatory, Infrastructure, AI Density
-- ============================================================================
-- These views return 0 rows initially but have correct schema for API contracts
-- As data sources are added, the queries will populate automatically
-- ============================================================================

-- 1. Innovation Velocity
-- Sources: Patents (WIPO), GitHub activity, Papers growth
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_innovation_velocity_by_country;

CREATE MATERIALIZED VIEW sofia.mv_innovation_velocity_by_country AS
SELECT 
    iso_alpha2 as country_code,
    0::int as patents_12m,
    0::numeric as patents_momentum,
    0::int as github_repos,
    0::int as papers_12m,
    0::numeric as innovation_score,
    'no_data'::text as innovation_tier,
    0::numeric(3,2) as confidence,
    NOW() as updated_at
FROM sofia.countries
WHERE iso_alpha2 IS NOT NULL
  AND FALSE;  -- Returns 0 rows initially

CREATE UNIQUE INDEX idx_mv_innov_cc ON sofia.mv_innovation_velocity_by_country(country_code);

-- 2. Brain Drain Index
-- Sources: Papers (author country) vs Jobs (company country)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_brain_drain_by_country;

-- Try to calculate from existing data
CREATE MATERIALIZED VIEW sofia.mv_brain_drain_by_country AS
WITH paper_production AS (
    SELECT 
        UNNEST(author_countries) as country_code,
        COUNT(*) as papers_produced
    FROM sofia.research_papers
    WHERE author_countries IS NOT NULL
      AND publication_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY UNNEST(author_countries)
),
talent_employment AS (
    SELECT 
        UPPER(SUBSTRING(country, 1, 2)) as country_code,
        COUNT(*) as jobs_available
    FROM sofia.jobs
    WHERE country IS NOT NULL
      AND posted_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY UPPER(SUBSTRING(country, 1, 2))
),
combined AS (
    SELECT 
        COALESCE(p.country_code, j.country_code) as country_code,
        COALESCE(p.papers_produced, 0) as papers_produced,
        COALESCE(j.jobs_available, 0) as jobs_available
    FROM paper_production p
    FULL OUTER JOIN talent_employment j ON p.country_code = j.country_code
)
SELECT 
    country_code,
    papers_produced,
    jobs_available,
    -- Brain drain index: Positive = exporting talent, Negative = importing
    CASE 
        WHEN papers_produced = 0 THEN 0
        ELSE ROUND(
            ((papers_produced - jobs_available)::numeric / GREATEST(papers_produced, 1)) * 100
        , 2)
    END as brain_drain_index,
    CASE 
        WHEN papers_produced > jobs_available * 1.5 THEN 'talent_exporter'
        WHEN jobs_available > papers_produced * 1.5 THEN 'talent_importer'
        ELSE 'balanced'
    END as brain_drain_tier,
    LEAST(1.0, GREATEST(0.0,
        0.5 * LEAST(1.0, papers_produced::numeric / 100) +
        0.5 * LEAST(1.0, jobs_available::numeric / 100)
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM combined
WHERE country_code IS NOT NULL
  AND LENGTH(country_code) = 2;

CREATE UNIQUE INDEX idx_mv_brain_cc ON sofia.mv_brain_drain_by_country(country_code);

-- 3. Regulatory Pressure (Scaffold - needs external source)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_regulatory_pressure_by_country;

CREATE MATERIALIZED VIEW sofia.mv_regulatory_pressure_by_country AS
SELECT 
    iso_alpha2 as country_code,
    0::int as regulations_count,
    0::numeric as regulatory_change_rate,
    0::numeric as compliance_cost_index,
    0::numeric as regulatory_pressure_score,
    'no_data'::text as pressure_tier,
    0::numeric(3,2) as confidence,
    NOW() as updated_at
FROM sofia.countries
WHERE iso_alpha2 IS NOT NULL
  AND FALSE;  -- Placeholder

CREATE UNIQUE INDEX idx_mv_regul_cc ON sofia.mv_regulatory_pressure_by_country(country_code);

-- 4. Infrastructure Stress (Scaffold - needs external source)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_infrastructure_stress_by_country;

CREATE MATERIALIZED VIEW sofia.mv_infrastructure_stress_by_country AS
SELECT 
    iso_alpha2 as country_code,
    0::numeric as infra_index,
    0::numeric as energy_reliability,
    0::numeric as connectivity_score,
    0::numeric as infrastructure_stress_score,
    'no_data'::text as stress_tier,
    0::numeric(3,2) as confidence,
    NOW() as updated_at
FROM sofia.countries
WHERE iso_alpha2 IS NOT NULL
  AND FALSE;  -- Placeholder

CREATE UNIQUE INDEX idx_mv_infra_cc ON sofia.mv_infrastructure_stress_by_country(country_code);

-- 5. AI Capability Density
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_ai_capability_density_by_country;

-- Attempt to calculate from AI-related papers and jobs
CREATE MATERIALIZED VIEW sofia.mv_ai_capability_density_by_country AS
WITH ai_papers AS (
    SELECT 
        UNNEST(author_countries) as country_code,
        COUNT(*) as ai_papers
    FROM sofia.research_papers
    WHERE author_countries IS NOT NULL
      AND (LOWER(title) LIKE '%artificial intelligence%' 
           OR LOWER(title) LIKE '%machine learning%'
           OR LOWER(title) LIKE '%deep learning%'
           OR LOWER(title) LIKE '%neural network%'
           OR primary_category ILIKE '%cs.AI%'
           OR primary_category ILIKE '%cs.LG%')
      AND publication_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY UNNEST(author_countries)
),
ai_jobs AS (
    SELECT 
        UPPER(SUBSTRING(country, 1, 2)) as country_code,
        COUNT(*) as ai_jobs
    FROM sofia.jobs
    WHERE country IS NOT NULL
      AND (LOWER(title) LIKE '%ai%'
           OR LOWER(title) LIKE '%machine learning%'
           OR LOWER(title) LIKE '%data scientist%'
           OR LOWER(description) LIKE '%artificial intelligence%')
      AND posted_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY UPPER(SUBSTRING(country, 1, 2))
),
combined AS (
    SELECT 
        COALESCE(p.country_code, j.country_code) as country_code,
        COALESCE(p.ai_papers, 0) as ai_papers,
        COALESCE(j.ai_jobs, 0) as ai_jobs
    FROM ai_papers p
    FULL OUTER JOIN ai_jobs j ON p.country_code = j.country_code
)
SELECT 
    country_code,
    ai_papers,
    ai_jobs,
    (ai_papers + ai_jobs) as ai_activity_total,
    -- Density score (normalized)
    LEAST(100, (ai_papers::numeric * 2 + ai_jobs::numeric)) as ai_density_score,
    CASE 
        WHEN (ai_papers + ai_jobs) >= 1000 THEN 'ai_leader'
        WHEN (ai_papers + ai_jobs) >= 100 THEN 'ai_active'
        WHEN (ai_papers + ai_jobs) >= 10 THEN 'ai_emerging'
        ELSE 'ai_nascent'
    END as ai_tier,
    LEAST(1.0, GREATEST(0.0,
        0.5 * LEAST(1.0, ai_papers::numeric / 50) +
        0.5 * LEAST(1.0, ai_jobs::numeric / 50)
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM combined
WHERE country_code IS NOT NULL
  AND LENGTH(country_code) = 2;

CREATE UNIQUE INDEX idx_mv_ai_cc ON sofia.mv_ai_capability_density_by_country(country_code);

-- ============================================================================
-- Refresh Instructions (add to cron after base data is available):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_innovation_velocity_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_brain_drain_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_regulatory_pressure_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_infrastructure_stress_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_ai_capability_density_by_country;
-- ============================================================================
