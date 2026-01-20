-- ============================================================================
-- Migration 009: Talent Intelligence Enterprise Upgrade
-- Purpose: Upgrade talent MVs with numeric confidence (0-1), momentum, 
--          and support for deterministic narratives
-- ============================================================================
-- Dependencies: 006_skill_gap_views.sql must be applied first
-- Refresh: CONCURRENTLY supported (has unique index on country_code)
-- ============================================================================

-- Drop and recreate with enterprise schema
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_skill_gap_country_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_skill_gap_by_country CASCADE;

-- Recreate mv_skill_gap_by_country with numeric confidence
CREATE MATERIALIZED VIEW sofia.mv_skill_gap_by_country AS
WITH demand AS (
    SELECT country_code, skill, demand_pct, job_count, total_jobs
    FROM sofia.mv_skill_demand_by_country
),
supply AS (
    SELECT country_code, skill, supply_pct, paper_count, total_papers, total_citations
    FROM sofia.mv_skill_supply_by_country
),
all_skills AS (
    SELECT DISTINCT skill FROM demand
    UNION
    SELECT DISTINCT skill FROM supply
),
all_countries AS (
    SELECT DISTINCT country_code FROM demand
    UNION
    SELECT DISTINCT country_code FROM supply
),
gap_calculation AS (
    SELECT 
        c.country_code,
        s.skill,
        COALESCE(d.demand_pct, 0) as demand_pct,
        COALESCE(sup.supply_pct, 0) as supply_pct,
        COALESCE(d.demand_pct, 0) - COALESCE(sup.supply_pct, 0) as gap_score,
        COALESCE(d.job_count, 0) as job_count,
        COALESCE(d.total_jobs, 0) as total_jobs,
        COALESCE(sup.paper_count, 0) as paper_count,
        COALESCE(sup.total_papers, 0) as total_papers,
        COALESCE(sup.total_citations, 0) as total_citations
    FROM all_countries c
    CROSS JOIN all_skills s
    LEFT JOIN demand d ON c.country_code = d.country_code AND s.skill = d.skill
    LEFT JOIN supply sup ON c.country_code = sup.country_code AND s.skill = sup.skill
    WHERE d.demand_pct IS NOT NULL OR sup.supply_pct IS NOT NULL
)
SELECT 
    country_code,
    skill,
    demand_pct,
    supply_pct,
    gap_score,
    -- Classificação do gap
    CASE 
        WHEN gap_score > 30 THEN 'market_hungry'
        WHEN gap_score < -30 THEN 'academia_ahead'
        WHEN ABS(gap_score) <= 10 THEN 'aligned'
        ELSE 'moderate_gap'
    END as gap_type,
    job_count,
    total_jobs,
    paper_count,
    total_papers,
    total_citations,
    -- ENTERPRISE: Numeric confidence score (0.0 - 1.0)
    LEAST(1.0, GREATEST(0.0,
        0.4 * LEAST(1.0, total_jobs::numeric / 100) +
        0.4 * LEAST(1.0, total_papers::numeric / 50) +
        0.2 * CASE WHEN job_count > 0 AND paper_count > 0 THEN 1.0 ELSE 0.5 END
    ))::numeric(3,2) as confidence,
    NOW() as calculated_at
FROM gap_calculation
ORDER BY country_code, ABS(gap_score) DESC;

-- Unique index for CONCURRENTLY refresh
CREATE UNIQUE INDEX idx_skill_gap_country_skill ON sofia.mv_skill_gap_by_country(country_code, skill);
CREATE INDEX idx_skill_gap_type ON sofia.mv_skill_gap_by_country(gap_type);

-- Recreate country summary with enterprise fields
CREATE MATERIALIZED VIEW sofia.mv_skill_gap_country_summary AS
WITH country_stats AS (
    SELECT 
        country_code,
        COUNT(DISTINCT skill) as skills_analyzed,
        ROUND(AVG(ABS(gap_score)), 2) as avg_gap_score,
        ROUND(AVG(CASE WHEN gap_score > 0 THEN gap_score ELSE 0 END), 2) as avg_demand_gap,
        ROUND(AVG(CASE WHEN gap_score < 0 THEN ABS(gap_score) ELSE 0 END), 2) as avg_supply_excess,
        SUM(job_count) as total_job_mentions,
        MAX(total_jobs) as total_jobs,
        SUM(paper_count) as total_paper_mentions,
        MAX(total_papers) as total_papers,
        -- Numeric confidence (aggregate)
        ROUND(AVG(confidence), 2) as confidence,
        -- Gap type counts for classification
        COUNT(*) FILTER (WHERE gap_type = 'market_hungry') as market_hungry_count,
        COUNT(*) FILTER (WHERE gap_type = 'academia_ahead') as academia_ahead_count,
        COUNT(*) FILTER (WHERE gap_type = 'aligned') as aligned_count
    FROM sofia.mv_skill_gap_by_country
    GROUP BY country_code
)
SELECT 
    cs.country_code,
    cs.skills_analyzed,
    cs.avg_gap_score,
    cs.avg_demand_gap,
    cs.avg_supply_excess,
    cs.total_job_mentions,
    cs.total_jobs,
    cs.total_paper_mentions,
    cs.total_papers,
    cs.confidence,
    -- Classification
    CASE 
        WHEN cs.avg_demand_gap > cs.avg_supply_excess * 1.5 THEN 'market_hungry'
        WHEN cs.avg_supply_excess > cs.avg_demand_gap * 1.5 THEN 'academia_ahead'
        WHEN cs.avg_gap_score < 10 THEN 'aligned'
        ELSE 'moderate_gap'
    END as overall_gap_type,
    -- Top skills (subquery approach for compatibility)
    (SELECT ARRAY_AGG(skill ORDER BY gap_score DESC) 
     FROM (SELECT skill, gap_score 
           FROM sofia.mv_skill_gap_by_country g2 
           WHERE g2.country_code = cs.country_code AND gap_score > 0 
           ORDER BY gap_score DESC LIMIT 3) x) as top_demand_gaps,
    (SELECT ARRAY_AGG(skill ORDER BY gap_score) 
     FROM (SELECT skill, gap_score 
           FROM sofia.mv_skill_gap_by_country g3 
           WHERE g3.country_code = cs.country_code AND gap_score < 0 
           ORDER BY gap_score LIMIT 3) y) as top_supply_excess,
    NOW() as updated_at
FROM country_stats cs;

-- Unique index for CONCURRENTLY refresh
CREATE UNIQUE INDEX idx_skill_gap_summary_cc ON sofia.mv_skill_gap_country_summary(country_code);

-- ============================================================================
-- Refresh Instructions (add to cron):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_demand_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_supply_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_gap_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_gap_country_summary;
-- ============================================================================
