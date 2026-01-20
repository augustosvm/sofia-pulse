-- Migration 008: Capital Analytics Intelligence (FIXED SCHEMA)
-- Purpose: Create analytics view for Capital Map with derived metrics (Momentum, Stage, Diversity)

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_capital_analytics;

CREATE MATERIALIZED VIEW sofia.mv_capital_analytics AS
WITH period_stats AS (
    SELECT 
        c.iso_alpha2 as country_code,
        -- Volume Current (Last 6 Months)
        COALESCE(SUM(CASE 
            WHEN fr.announced_date >= CURRENT_DATE - INTERVAL '6 months' 
            THEN fr.amount_usd ELSE 0 END), 0) as vol_6m,
        
        -- Volume Previous (6-12 Months ago)
        COALESCE(SUM(CASE 
            WHEN fr.announced_date >= CURRENT_DATE - INTERVAL '12 months' 
             AND fr.announced_date < CURRENT_DATE - INTERVAL '6 months'
            THEN fr.amount_usd ELSE 0 END), 0) as vol_prev_6m,
            
        -- Deal Counts
        COUNT(CASE WHEN fr.announced_date >= CURRENT_DATE - INTERVAL '12 months' THEN 1 END) as deals_12m,
        
        -- Avg Ticket (12m basis for stability)
        COALESCE(AVG(fr.amount_usd) FILTER (WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '12 months'), 0) as avg_ticket_12m,
        
        -- Sector Aggregation for Diversity Check
        MODE() WITHIN GROUP (ORDER BY fr.sector) as top_sector,
        COUNT(DISTINCT fr.sector) as sector_count
    FROM sofia.funding_rounds fr
    JOIN sofia.countries c ON fr.country_id = c.id
    WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '12 months'
      AND c.iso_alpha2 IS NOT NULL
    GROUP BY c.iso_alpha2
),
metrics AS (
    SELECT
        country_code,
        vol_6m,
        vol_prev_6m,
        (vol_6m + vol_prev_6m) as total_vol_12m,
        deals_12m,
        avg_ticket_12m,
        top_sector,
        sector_count,
        
        -- Momentum Calculation
        CASE 
            WHEN vol_prev_6m > 0 THEN ((vol_6m - vol_prev_6m)::numeric / vol_prev_6m)
            WHEN vol_6m > 0 THEN 1.0 -- New active market (100% growth proxy)
            ELSE 0 
        END as momentum_pct,
        
        -- Stage Proxy
        CASE 
            WHEN avg_ticket_12m > 50000000 THEN 'late_growth' -- >$50M
            WHEN avg_ticket_12m > 10000000 THEN 'mid_growth'  -- $10M-$50M
            WHEN avg_ticket_12m > 2000000 THEN 'early_stage'  -- $2M-$10M
            ELSE 'seed_stage'                                   -- <$2M
        END as market_stage,

        -- Confidence Score Logic (Simple heuristic)
        CASE
            WHEN deals_12m >= 50 THEN 1.0   -- High confidence
            WHEN deals_12m >= 10 THEN 0.8   -- Medium
            WHEN deals_12m >= 5 THEN 0.5    -- Low
            ELSE 0.3                        -- Very Low (Partial)
        END as confidence_score
    FROM period_stats
)
SELECT * FROM metrics
ORDER BY total_vol_12m DESC;

CREATE INDEX idx_mv_cap_analytics_country ON sofia.mv_capital_analytics(country_code);
