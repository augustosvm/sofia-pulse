-- ============================================================================
-- AI Technology Radar - SQL Views & Metrics
-- Created: 2025-12-04
-- Purpose: Comprehensive views for AI technology trend analysis
-- ============================================================================

-- ============================================================================
-- 1. GitHub Metrics View (with momentum calculations)
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_github_metrics AS
WITH daily_data AS (
    SELECT
        tech_key,
        category,
        date,
        total_stars,
        total_repos,
        stars_30d,
        stars_7d,
        LAG(total_stars, 7) OVER (PARTITION BY tech_key ORDER BY date) as stars_7d_ago,
        LAG(total_stars, 30) OVER (PARTITION BY tech_key ORDER BY date) as stars_30d_ago
    FROM sofia.ai_github_trends
),
latest AS (
    SELECT DISTINCT ON (tech_key)
        tech_key,
        category,
        date,
        total_stars,
        total_repos,
        stars_30d,
        stars_7d,
        stars_7d_ago,
        stars_30d_ago
    FROM daily_data
    ORDER BY tech_key, date DESC
)
SELECT
    tech_key,
    category,
    date,
    total_stars,
    total_repos,
    stars_30d,
    stars_7d,

    -- Momentum calculations (percentage growth)
    CASE
        WHEN stars_7d_ago > 0 THEN
            ROUND(((total_stars - stars_7d_ago)::NUMERIC / stars_7d_ago * 100), 2)
        ELSE 0
    END as momentum_7d,

    CASE
        WHEN stars_30d_ago > 0 THEN
            ROUND(((total_stars - stars_30d_ago)::NUMERIC / stars_30d_ago * 100), 2)
        ELSE 0
    END as momentum_30d,

    -- Growth rate (annualized based on 30d growth)
    CASE
        WHEN stars_30d_ago > 0 AND total_stars > stars_30d_ago THEN
            ROUND((POWER((total_stars::NUMERIC / stars_30d_ago), 365.0/30) - 1) * 100, 2)
        ELSE 0
    END as growth_rate_annual,

    -- Velocity (new stars per day)
    ROUND(stars_30d::NUMERIC / 30, 2) as velocity_daily

FROM latest;

COMMENT ON VIEW sofia.ai_github_metrics IS 'GitHub AI technology metrics with momentum, growth rate, and velocity calculations';

-- ============================================================================
-- 2. PyPI Metrics View
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_pypi_metrics AS
WITH daily_data AS (
    SELECT
        tech_key,
        category,
        package_name,
        date,
        downloads_30d,
        downloads_7d,
        LAG(downloads_30d, 7) OVER (PARTITION BY package_name ORDER BY date) as downloads_7d_ago,
        LAG(downloads_30d, 30) OVER (PARTITION BY package_name ORDER BY date) as downloads_30d_ago
    FROM sofia.ai_pypi_packages
),
latest AS (
    SELECT DISTINCT ON (package_name)
        tech_key,
        category,
        package_name,
        date,
        downloads_30d,
        downloads_7d,
        downloads_7d_ago,
        downloads_30d_ago
    FROM daily_data
    ORDER BY package_name, date DESC
)
SELECT
    tech_key,
    category,
    package_name,
    date,
    downloads_30d,
    downloads_7d,

    -- Momentum calculations
    CASE
        WHEN downloads_7d_ago > 0 THEN
            ROUND(((downloads_30d - downloads_7d_ago)::NUMERIC / downloads_7d_ago * 100), 2)
        ELSE 0
    END as momentum_7d,

    CASE
        WHEN downloads_30d_ago > 0 THEN
            ROUND(((downloads_30d - downloads_30d_ago)::NUMERIC / downloads_30d_ago * 100), 2)
        ELSE 0
    END as momentum_30d,

    -- Growth rate
    CASE
        WHEN downloads_30d_ago > 0 AND downloads_30d > downloads_30d_ago THEN
            ROUND((POWER((downloads_30d::NUMERIC / downloads_30d_ago), 365.0/30) - 1) * 100, 2)
        ELSE 0
    END as growth_rate_annual,

    -- Velocity
    ROUND(downloads_30d::NUMERIC / 30, 0) as velocity_daily

FROM latest;

COMMENT ON VIEW sofia.ai_pypi_metrics IS 'PyPI AI package metrics with momentum and growth calculations';

-- ============================================================================
-- 3. NPM Metrics View
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_npm_metrics AS
WITH daily_data AS (
    SELECT
        tech_key,
        category,
        package_name,
        date,
        downloads_30d,
        downloads_7d,
        LAG(downloads_30d, 7) OVER (PARTITION BY package_name ORDER BY date) as downloads_7d_ago,
        LAG(downloads_30d, 30) OVER (PARTITION BY package_name ORDER BY date) as downloads_30d_ago
    FROM sofia.ai_npm_packages
),
latest AS (
    SELECT DISTINCT ON (package_name)
        tech_key,
        category,
        package_name,
        date,
        downloads_30d,
        downloads_7d,
        downloads_7d_ago,
        downloads_30d_ago
    FROM daily_data
    ORDER BY package_name, date DESC
)
SELECT
    tech_key,
    category,
    package_name,
    date,
    downloads_30d,
    downloads_7d,

    -- Momentum calculations
    CASE
        WHEN downloads_7d_ago > 0 THEN
            ROUND(((downloads_30d - downloads_7d_ago)::NUMERIC / downloads_7d_ago * 100), 2)
        ELSE 0
    END as momentum_7d,

    CASE
        WHEN downloads_30d_ago > 0 THEN
            ROUND(((downloads_30d - downloads_30d_ago)::NUMERIC / downloads_30d_ago * 100), 2)
        ELSE 0
    END as momentum_30d,

    -- Growth rate
    CASE
        WHEN downloads_30d_ago > 0 AND downloads_30d > downloads_30d_ago THEN
            ROUND((POWER((downloads_30d::NUMERIC / downloads_30d_ago), 365.0/30) - 1) * 100, 2)
        ELSE 0
    END as growth_rate_annual,

    -- Velocity
    ROUND(downloads_30d::NUMERIC / 30, 0) as velocity_daily

FROM latest;

COMMENT ON VIEW sofia.ai_npm_metrics IS 'NPM AI package metrics with momentum and growth calculations';

-- ============================================================================
-- 4. HuggingFace Metrics View
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_huggingface_metrics AS
WITH daily_data AS (
    SELECT
        tech_key,
        category,
        model_id,
        date,
        likes,
        downloads_total,
        LAG(likes, 7) OVER (PARTITION BY model_id ORDER BY date) as likes_7d_ago,
        LAG(likes, 30) OVER (PARTITION BY model_id ORDER BY date) as likes_30d_ago,
        LAG(downloads_total, 7) OVER (PARTITION BY model_id ORDER BY date) as downloads_7d_ago,
        LAG(downloads_total, 30) OVER (PARTITION BY model_id ORDER BY date) as downloads_30d_ago
    FROM sofia.ai_huggingface_models
),
latest AS (
    SELECT DISTINCT ON (model_id)
        tech_key,
        category,
        model_id,
        date,
        likes,
        downloads_total,
        likes_7d_ago,
        likes_30d_ago,
        downloads_7d_ago,
        downloads_30d_ago
    FROM daily_data
    ORDER BY model_id, date DESC
)
SELECT
    tech_key,
    category,
    model_id,
    date,
    likes,
    downloads_total,

    -- Momentum calculations (likes)
    CASE
        WHEN likes_7d_ago > 0 THEN
            ROUND(((likes - likes_7d_ago)::NUMERIC / likes_7d_ago * 100), 2)
        ELSE 0
    END as likes_momentum_7d,

    CASE
        WHEN likes_30d_ago > 0 THEN
            ROUND(((likes - likes_30d_ago)::NUMERIC / likes_30d_ago * 100), 2)
        ELSE 0
    END as likes_momentum_30d,

    -- Momentum calculations (downloads)
    CASE
        WHEN downloads_7d_ago > 0 THEN
            ROUND(((downloads_total - downloads_7d_ago)::NUMERIC / downloads_7d_ago * 100), 2)
        ELSE 0
    END as downloads_momentum_7d,

    CASE
        WHEN downloads_30d_ago > 0 THEN
            ROUND(((downloads_total - downloads_30d_ago)::NUMERIC / downloads_30d_ago * 100), 2)
        ELSE 0
    END as downloads_momentum_30d

FROM latest;

COMMENT ON VIEW sofia.ai_huggingface_metrics IS 'HuggingFace model metrics with momentum calculations';

-- ============================================================================
-- 5. ArXiv Metrics View (trending research topics)
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_arxiv_metrics AS
WITH monthly_data AS (
    SELECT
        tech_key,
        category,
        keyword,
        year,
        month,
        paper_count,
        LAG(paper_count, 1) OVER (PARTITION BY keyword ORDER BY year, month) as papers_prev_month,
        LAG(paper_count, 3) OVER (PARTITION BY keyword ORDER BY year, month) as papers_3mo_ago,
        LAG(paper_count, 6) OVER (PARTITION BY keyword ORDER BY year, month) as papers_6mo_ago
    FROM sofia.ai_arxiv_keywords
),
latest AS (
    SELECT DISTINCT ON (keyword)
        tech_key,
        category,
        keyword,
        year,
        month,
        paper_count,
        papers_prev_month,
        papers_3mo_ago,
        papers_6mo_ago
    FROM monthly_data
    ORDER BY keyword, year DESC, month DESC
)
SELECT
    tech_key,
    category,
    keyword,
    year,
    month,
    paper_count,

    -- Month-over-month growth
    CASE
        WHEN papers_prev_month > 0 THEN
            ROUND(((paper_count - papers_prev_month)::NUMERIC / papers_prev_month * 100), 2)
        ELSE 0
    END as momentum_mom,

    -- 3-month growth
    CASE
        WHEN papers_3mo_ago > 0 THEN
            ROUND(((paper_count - papers_3mo_ago)::NUMERIC / papers_3mo_ago * 100), 2)
        ELSE 0
    END as momentum_3mo,

    -- 6-month growth
    CASE
        WHEN papers_6mo_ago > 0 THEN
            ROUND(((paper_count - papers_6mo_ago)::NUMERIC / papers_6mo_ago * 100), 2)
        ELSE 0
    END as momentum_6mo

FROM latest;

COMMENT ON VIEW sofia.ai_arxiv_metrics IS 'ArXiv AI research paper trends with momentum calculations';

-- ============================================================================
-- 6. CONSOLIDATED AI TECH RADAR VIEW
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_tech_radar_consolidated AS
WITH
-- Aggregate GitHub data by tech_key
github_agg AS (
    SELECT
        tech_key,
        category,
        SUM(total_stars) as github_stars,
        SUM(total_repos) as github_repos,
        AVG(momentum_30d) as github_momentum,
        AVG(velocity_daily) as github_velocity
    FROM sofia.ai_github_metrics
    GROUP BY tech_key, category
),
-- Aggregate PyPI data by tech_key
pypi_agg AS (
    SELECT
        tech_key,
        category,
        SUM(downloads_30d) as pypi_downloads,
        AVG(momentum_30d) as pypi_momentum
    FROM sofia.ai_pypi_metrics
    GROUP BY tech_key, category
),
-- Aggregate NPM data by tech_key
npm_agg AS (
    SELECT
        tech_key,
        category,
        SUM(downloads_30d) as npm_downloads,
        AVG(momentum_30d) as npm_momentum
    FROM sofia.ai_npm_metrics
    GROUP BY tech_key, category
),
-- Aggregate HuggingFace data by tech_key
hf_agg AS (
    SELECT
        tech_key,
        category,
        SUM(likes) as hf_likes,
        SUM(downloads_total) as hf_downloads,
        AVG(likes_momentum_30d) as hf_momentum
    FROM sofia.ai_huggingface_metrics
    GROUP BY tech_key, category
),
-- Aggregate ArXiv data by tech_key
arxiv_agg AS (
    SELECT
        tech_key,
        category,
        SUM(paper_count) as arxiv_papers,
        AVG(momentum_3mo) as arxiv_momentum
    FROM sofia.ai_arxiv_metrics
    GROUP BY tech_key, category
)
-- Combine all sources
SELECT
    COALESCE(g.tech_key, p.tech_key, n.tech_key, h.tech_key, a.tech_key) as tech_key,
    COALESCE(g.category, p.category, n.category, h.category, a.category) as category,

    -- Get display name from categories table
    c.display_name,

    -- GitHub metrics
    COALESCE(g.github_stars, 0) as github_stars,
    COALESCE(g.github_repos, 0) as github_repos,
    COALESCE(g.github_momentum, 0) as github_momentum_30d,
    COALESCE(g.github_velocity, 0) as github_velocity_daily,

    -- PyPI metrics
    COALESCE(p.pypi_downloads, 0) as pypi_downloads_30d,
    COALESCE(p.pypi_momentum, 0) as pypi_momentum_30d,

    -- NPM metrics
    COALESCE(n.npm_downloads, 0) as npm_downloads_30d,
    COALESCE(n.npm_momentum, 0) as npm_momentum_30d,

    -- HuggingFace metrics
    COALESCE(h.hf_likes, 0) as hf_likes,
    COALESCE(h.hf_downloads, 0) as hf_downloads,
    COALESCE(h.hf_momentum, 0) as hf_momentum_30d,

    -- ArXiv metrics
    COALESCE(a.arxiv_papers, 0) as arxiv_papers_monthly,
    COALESCE(a.arxiv_momentum, 0) as arxiv_momentum_3mo,

    -- Composite scores (normalized 0-100)
    -- Developer adoption score (GitHub + PyPI + NPM)
    ROUND(
        (
            LEAST(COALESCE(g.github_stars, 0)::NUMERIC / 10000, 1) * 40 +
            LEAST(COALESCE(p.pypi_downloads, 0)::NUMERIC / 10000000, 1) * 30 +
            LEAST(COALESCE(n.npm_downloads, 0)::NUMERIC / 10000000, 1) * 30
        ) * 100,
        2
    ) as developer_adoption_score,

    -- Research interest score (ArXiv + HuggingFace)
    ROUND(
        (
            LEAST(COALESCE(a.arxiv_papers, 0)::NUMERIC / 100, 1) * 60 +
            LEAST(COALESCE(h.hf_likes, 0)::NUMERIC / 1000, 1) * 40
        ) * 100,
        2
    ) as research_interest_score,

    -- Overall hype score (weighted average of all signals)
    ROUND(
        (
            LEAST(COALESCE(g.github_stars, 0)::NUMERIC / 10000, 1) * 25 +
            LEAST(COALESCE(p.pypi_downloads, 0)::NUMERIC / 10000000, 1) * 20 +
            LEAST(COALESCE(n.npm_downloads, 0)::NUMERIC / 10000000, 1) * 15 +
            LEAST(COALESCE(h.hf_likes, 0)::NUMERIC / 1000, 1) * 20 +
            LEAST(COALESCE(a.arxiv_papers, 0)::NUMERIC / 100, 1) * 20
        ) * 100,
        2
    ) as hype_index,

    -- Overall momentum (average of all momentums)
    ROUND(
        (
            COALESCE(g.github_momentum, 0) +
            COALESCE(p.pypi_momentum, 0) +
            COALESCE(n.npm_momentum, 0) +
            COALESCE(h.hf_momentum, 0) +
            COALESCE(a.arxiv_momentum, 0)
        ) / 5.0,
        2
    ) as overall_momentum,

    -- Timestamp
    NOW() as computed_at

FROM github_agg g
FULL OUTER JOIN pypi_agg p USING (tech_key, category)
FULL OUTER JOIN npm_agg n USING (tech_key, category)
FULL OUTER JOIN hf_agg h USING (tech_key, category)
FULL OUTER JOIN arxiv_agg a USING (tech_key, category)
LEFT JOIN sofia.ai_tech_categories c ON c.tech_key = COALESCE(g.tech_key, p.tech_key, n.tech_key, h.tech_key, a.tech_key);

COMMENT ON VIEW sofia.ai_tech_radar_consolidated IS 'Consolidated AI Technology Radar with composite scores: developer_adoption_score, research_interest_score, hype_index, and overall_momentum';

-- ============================================================================
-- 7. Top Technologies by Category
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_top_technologies_by_category AS
SELECT
    category,
    tech_key,
    display_name,
    hype_index,
    overall_momentum,
    developer_adoption_score,
    research_interest_score,
    github_stars,
    pypi_downloads_30d,
    npm_downloads_30d,
    hf_likes,
    arxiv_papers_monthly,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY hype_index DESC) as rank_in_category
FROM sofia.ai_tech_radar_consolidated
ORDER BY category, rank_in_category;

COMMENT ON VIEW sofia.ai_top_technologies_by_category IS 'AI technologies ranked by hype_index within each category';

-- ============================================================================
-- 8. Rising Stars (highest momentum)
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_rising_stars AS
SELECT
    tech_key,
    category,
    display_name,
    hype_index,
    overall_momentum,
    github_momentum_30d,
    pypi_momentum_30d,
    npm_momentum_30d,
    hf_momentum_30d,
    arxiv_momentum_3mo
FROM sofia.ai_tech_radar_consolidated
WHERE overall_momentum > 10  -- At least 10% growth
ORDER BY overall_momentum DESC
LIMIT 50;

COMMENT ON VIEW sofia.ai_rising_stars IS 'AI technologies with highest momentum (fastest growing)';

-- ============================================================================
-- 9. Dark Horses (high growth, low current visibility)
-- ============================================================================
CREATE OR REPLACE VIEW sofia.ai_dark_horses AS
SELECT
    tech_key,
    category,
    display_name,
    hype_index,
    overall_momentum,
    github_stars,
    github_momentum_30d,
    developer_adoption_score
FROM sofia.ai_tech_radar_consolidated
WHERE
    overall_momentum > 20         -- High momentum
    AND hype_index < 30          -- But low current visibility
ORDER BY overall_momentum DESC;

COMMENT ON VIEW sofia.ai_dark_horses IS 'AI technologies with high momentum but low current visibility (potential breakouts)';

-- ============================================================================
-- Grant permissions (if needed)
-- ============================================================================
-- GRANT SELECT ON ALL TABLES IN SCHEMA sofia TO sofia_reader;
