-- ============================================================================
-- CAPITAL FLOW MAP VIEW
-- Aggregates funding data by country for map visualization
-- ============================================================================

-- Drop existing view if exists
DROP VIEW IF EXISTS sofia.v_capital_by_country CASCADE;

-- Create view for capital flow by country
CREATE OR REPLACE VIEW sofia.v_capital_by_country AS
SELECT 
    COALESCE(country_code, 'XX') as country_code,
    COUNT(*) as deal_count,
    COALESCE(SUM(amount_usd), 0) as total_usd,
    COALESCE(AVG(amount_usd), 0) as avg_usd,
    MAX(announced_date) as last_deal_date
FROM sofia.funding_rounds
WHERE announced_date >= CURRENT_DATE - INTERVAL '365 days'
    AND country_code IS NOT NULL
    AND country_code != ''
GROUP BY country_code
ORDER BY total_usd DESC NULLS LAST;

-- Create index for faster queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_funding_country_date 
ON sofia.funding_rounds(country_code, announced_date);

-- Materialized view for better performance (optional)
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_capital_by_country CASCADE;

CREATE MATERIALIZED VIEW sofia.mv_capital_by_country AS
SELECT 
    COALESCE(country_code, 'XX') as country_code,
    COUNT(*) as deal_count,
    COALESCE(SUM(amount_usd), 0) as total_usd,
    COALESCE(AVG(amount_usd), 0) as avg_usd,
    array_agg(DISTINCT sector) FILTER (WHERE sector IS NOT NULL) as sectors,
    MAX(announced_date) as last_deal_date
FROM sofia.funding_rounds
WHERE announced_date >= CURRENT_DATE - INTERVAL '365 days'
    AND country_code IS NOT NULL
    AND country_code != ''
GROUP BY country_code
ORDER BY total_usd DESC NULLS LAST;

-- Create unique index for faster refreshes
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_capital_country 
ON sofia.mv_capital_by_country(country_code);

-- Comment
COMMENT ON MATERIALIZED VIEW sofia.mv_capital_by_country IS 
'Aggregated capital flow by country (365 days window) for map visualization';
