-- ============================================================================
-- Migration 013: Intelligence Expansion - Real Data Domains
-- Purpose: Implement 3 new intelligence domains using existing collector data
-- Domains: Research Velocity, Conference Gravity, Tool Demand
-- ============================================================================

-- ============================================================================
-- 1. RESEARCH VELOCITY INDEX
-- Source: sofia.research_papers (from research-papers-collector.ts)
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_research_velocity_by_country;

CREATE MATERIALIZED VIEW sofia.mv_research_velocity_by_country AS
WITH papers_by_country AS (
    SELECT 
        UNNEST(author_countries) as country_code,
        publication_date,
        primary_category,
        cited_by_count
    FROM sofia.research_papers
    WHERE author_countries IS NOT NULL
      AND publication_date IS NOT NULL
),
period_stats AS (
    SELECT 
        country_code,
        COUNT(*) FILTER (WHERE publication_date >= CURRENT_DATE - INTERVAL '6 months') as papers_6m,
        COUNT(*) FILTER (WHERE publication_date >= CURRENT_DATE - INTERVAL '12 months' 
                          AND publication_date < CURRENT_DATE - INTERVAL '6 months') as papers_prev_6m,
        COUNT(*) FILTER (WHERE publication_date >= CURRENT_DATE - INTERVAL '12 months') as papers_12m,
        SUM(cited_by_count) FILTER (WHERE publication_date >= CURRENT_DATE - INTERVAL '12 months') as citations_12m,
        MODE() WITHIN GROUP (ORDER BY primary_category) as top_category,
        COUNT(DISTINCT primary_category) as category_diversity
    FROM papers_by_country
    GROUP BY country_code
    HAVING COUNT(*) >= 5  -- Minimum threshold
)
SELECT 
    country_code,
    papers_12m,
    papers_6m,
    papers_prev_6m,
    COALESCE(citations_12m, 0) as citations_12m,
    top_category,
    category_diversity,
    -- Momentum: growth rate
    CASE 
        WHEN papers_prev_6m > 0 THEN ROUND(((papers_6m - papers_prev_6m)::numeric / papers_prev_6m) * 100, 2)
        WHEN papers_6m > 0 THEN 100.0  -- New activity
        ELSE 0
    END as momentum_pct,
    -- Research intensity per paper (citations proxy)
    CASE 
        WHEN papers_12m > 0 THEN ROUND((COALESCE(citations_12m, 0)::numeric / papers_12m), 2)
        ELSE 0
    END as avg_citations,
    -- Velocity tier
    CASE 
        WHEN papers_12m >= 1000 THEN 'research_powerhouse'
        WHEN papers_12m >= 100 THEN 'research_active'
        WHEN papers_12m >= 20 THEN 'research_emerging'
        ELSE 'research_nascent'
    END as velocity_tier,
    -- Confidence score
    LEAST(1.0, GREATEST(0.0,
        0.5 * LEAST(1.0, papers_12m::numeric / 200) +
        0.3 * LEAST(1.0, category_diversity::numeric / 10) +
        0.2 * CASE WHEN papers_6m > 0 THEN 1.0 ELSE 0.5 END
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM period_stats
WHERE country_code IS NOT NULL
  AND LENGTH(country_code) = 2
ORDER BY papers_12m DESC;

CREATE UNIQUE INDEX idx_mv_research_vel_cc ON sofia.mv_research_velocity_by_country(country_code);

-- ============================================================================
-- 2. CONFERENCE GRAVITY INDEX
-- Source: sofia.tech_conferences (from tech-conferences-collector.ts)
-- ============================================================================

-- First check if tech_conferences exists, if not create scaffold
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_schema = 'sofia' AND table_name = 'tech_conferences') THEN
        CREATE TABLE sofia.tech_conferences (
            id SERIAL PRIMARY KEY,
            name TEXT,
            location TEXT,
            country TEXT,
            country_code CHAR(2),
            start_date DATE,
            end_date DATE,
            tier TEXT,  -- major/minor
            attendees_estimate INT,
            topics TEXT[],
            url TEXT,
            collected_at TIMESTAMP DEFAULT NOW()
        );
    END IF;
END $$;

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_conference_gravity_by_country;

CREATE MATERIALIZED VIEW sofia.mv_conference_gravity_by_country AS
WITH conf_stats AS (
    SELECT 
        COALESCE(country_code, UPPER(SUBSTRING(country, 1, 2))) as country_code,
        COUNT(*) as conference_count,
        COUNT(*) FILTER (WHERE tier = 'major' OR attendees_estimate > 1000) as major_conferences,
        SUM(COALESCE(attendees_estimate, 200)) as total_attendees_estimate,
        COUNT(DISTINCT EXTRACT(MONTH FROM start_date)) as months_active
    FROM sofia.tech_conferences
    WHERE start_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY COALESCE(country_code, UPPER(SUBSTRING(country, 1, 2)))
)
SELECT 
    country_code,
    conference_count,
    major_conferences,
    total_attendees_estimate,
    months_active,
    -- Gravity score
    ROUND((conference_count * 10 + major_conferences * 50 + total_attendees_estimate / 100)::numeric, 0) as gravity_score,
    -- Tier
    CASE 
        WHEN conference_count >= 50 OR major_conferences >= 10 THEN 'conference_hub'
        WHEN conference_count >= 10 OR major_conferences >= 3 THEN 'conference_active'
        WHEN conference_count >= 3 THEN 'conference_emerging'
        ELSE 'conference_minimal'
    END as gravity_tier,
    -- Year-round or seasonal
    CASE 
        WHEN months_active >= 10 THEN 'year_round'
        WHEN months_active >= 6 THEN 'multi_season'
        ELSE 'seasonal'
    END as seasonality,
    -- Confidence
    LEAST(1.0, GREATEST(0.0,
        0.6 * LEAST(1.0, conference_count::numeric / 20) +
        0.4 * LEAST(1.0, major_conferences::numeric / 5)
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM conf_stats
WHERE country_code IS NOT NULL
  AND LENGTH(country_code) = 2
  AND conference_count > 0
ORDER BY gravity_score DESC;

CREATE UNIQUE INDEX idx_mv_conf_gravity_cc ON sofia.mv_conference_gravity_by_country(country_code);

-- ============================================================================
-- 3. TOOL DEMAND INDEX
-- Source: sofia.jobs (skills mentions) + sofia.developer_tools
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_tool_demand_by_country;

CREATE MATERIALIZED VIEW sofia.mv_tool_demand_by_country AS
WITH tool_keywords AS (
    -- Top developer tools to track
    SELECT unnest(ARRAY[
        'docker', 'kubernetes', 'terraform', 'aws', 'azure', 'gcp',
        'react', 'angular', 'vue', 'node', 'python', 'java', 'golang',
        'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'jenkins', 'github', 'gitlab', 'jira', 'confluence',
        'datadog', 'grafana', 'prometheus', 'kafka', 'rabbitmq'
    ]) as tool
),
job_tool_matches AS (
    SELECT 
        UPPER(SUBSTRING(j.country, 1, 2)) as country_code,
        t.tool,
        COUNT(*) as mention_count
    FROM sofia.jobs j
    CROSS JOIN tool_keywords t
    WHERE j.posted_date >= CURRENT_DATE - INTERVAL '90 days'
      AND j.description IS NOT NULL
      AND LOWER(j.description) LIKE '%' || t.tool || '%'
    GROUP BY UPPER(SUBSTRING(j.country, 1, 2)), t.tool
),
country_totals AS (
    SELECT 
        country_code,
        SUM(mention_count) as total_tool_mentions,
        COUNT(DISTINCT tool) as tools_diversity,
        MODE() WITHIN GROUP (ORDER BY mention_count DESC) as top_tool,
        MAX(mention_count) as top_tool_mentions
    FROM job_tool_matches
    GROUP BY country_code
)
SELECT 
    ct.country_code,
    ct.total_tool_mentions,
    ct.tools_diversity,
    ct.top_tool,
    ct.top_tool_mentions,
    -- Modernity score: diversity + cloud tool presence
    ROUND((ct.tools_diversity * 3 + ct.total_tool_mentions / 10)::numeric, 0) as tool_demand_score,
    -- Tier
    CASE 
        WHEN ct.tools_diversity >= 20 THEN 'modern_stack'
        WHEN ct.tools_diversity >= 10 THEN 'diverse_stack'
        WHEN ct.tools_diversity >= 5 THEN 'standard_stack'
        ELSE 'limited_stack'
    END as stack_tier,
    -- Confidence
    LEAST(1.0, GREATEST(0.0,
        0.5 * LEAST(1.0, ct.total_tool_mentions::numeric / 1000) +
        0.5 * LEAST(1.0, ct.tools_diversity::numeric / 20)
    ))::numeric(3,2) as confidence,
    NOW() as updated_at
FROM country_totals ct
WHERE ct.country_code IS NOT NULL
  AND LENGTH(ct.country_code) = 2
ORDER BY tool_demand_score DESC;

CREATE UNIQUE INDEX idx_mv_tool_demand_cc ON sofia.mv_tool_demand_by_country(country_code);

-- ============================================================================
-- Refresh Instructions:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_research_velocity_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_conference_gravity_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_tool_demand_by_country;
-- ============================================================================
