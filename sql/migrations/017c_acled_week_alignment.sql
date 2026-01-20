-- ============================================================================
-- Migration 017c: ACLED Week Alignment Fix
-- Purpose: Add week_start column for proper week-aligned filtering
-- Issue: 197k rows have week != date_trunc('week', week) causing filter bugs
-- ============================================================================

-- Check if week_start already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sofia' 
          AND table_name = 'acled_aggregated' 
          AND column_name = 'week_start'
    ) THEN
        -- Add week_start column
        ALTER TABLE sofia.acled_aggregated 
        ADD COLUMN week_start DATE;
        
        RAISE NOTICE 'Added week_start column to acled_aggregated';
    ELSE
        RAISE NOTICE 'week_start column already exists, skipping';
    END IF;
END $$;

-- Backfill week_start with normalized week values
UPDATE sofia.acled_aggregated 
SET week_start = date_trunc('week', week)::date 
WHERE week_start IS NULL;

-- Create index for performance (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'sofia' 
          AND tablename = 'acled_aggregated' 
          AND indexname = 'idx_acled_aggregated_week_start'
    ) THEN
        CREATE INDEX idx_acled_aggregated_week_start 
        ON sofia.acled_aggregated(week_start);
        
        RAISE NOTICE 'Created index on week_start';
    ELSE
        RAISE NOTICE 'Index idx_acled_aggregated_week_start already exists';
    END IF;
END $$;

-- Create composite index for country + week_start queries
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'sofia' 
          AND tablename = 'acled_aggregated' 
          AND indexname = 'idx_acled_aggregated_country_week_start'
    ) THEN
        CREATE INDEX idx_acled_aggregated_country_week_start 
        ON sofia.acled_aggregated(country_id, week_start);
        
        RAISE NOTICE 'Created composite index on country_id, week_start';
    END IF;
END $$;

COMMENT ON COLUMN sofia.acled_aggregated.week_start IS 
'Week-aligned date (Monday) for deterministic time window filtering. Always date_trunc(week, week)::date';

-- ============================================================================
-- Update Women Intelligence MV to use week_start
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS sofia.mv_women_intelligence_by_country;

CREATE MATERIALIZED VIEW sofia.mv_women_intelligence_by_country AS
WITH violence_stats AS (
    SELECT 
        c.iso_alpha2 AS country_code,
        SUM(a.events) FILTER (WHERE COALESCE(a.week_start, date_trunc('week', a.week)::date) >= date_trunc('week', CURRENT_DATE)::date - interval '4 weeks') AS events_30d,
        SUM(a.events) FILTER (WHERE COALESCE(a.week_start, date_trunc('week', a.week)::date) >= date_trunc('week', CURRENT_DATE)::date - interval '13 weeks') AS events_90d,
        SUM(a.fatalities) FILTER (WHERE COALESCE(a.week_start, date_trunc('week', a.week)::date) >= date_trunc('week', CURRENT_DATE)::date - interval '13 weeks') AS fatalities_90d,
        COUNT(DISTINCT a.event_type) AS event_type_diversity
    FROM sofia.acled_aggregated a
    JOIN sofia.countries c ON a.country_id = c.id
    WHERE c.iso_alpha2 IS NOT NULL
      AND COALESCE(a.week_start, date_trunc('week', a.week)::date) >= date_trunc('week', CURRENT_DATE)::date - interval '26 weeks'
    GROUP BY c.iso_alpha2
)
SELECT 
    c.iso_alpha2 AS country_code,
    COALESCE(vs.events_30d, 0) AS events_30d,
    COALESCE(vs.events_90d, 0) AS events_90d,
    COALESCE(vs.fatalities_90d, 0) AS fatalities_90d,
    NULL::integer AS women_specific_events,
    COALESCE(vs.event_type_diversity, 0) AS event_type_diversity,
    'proxy_general_violence'::text AS data_scope,
    CASE 
        WHEN COALESCE(vs.events_90d, 0) > 0 
        THEN ROUND((COALESCE(vs.events_30d, 0)::numeric / NULLIF(COALESCE(vs.events_90d, 0) / 3.0, 0)), 2)
        ELSE 0
    END AS violence_momentum,
    LEAST(100, ROUND(
        (COALESCE(vs.events_30d, 0) * 2 + 
         COALESCE(vs.fatalities_90d, 0) * 0.5)::numeric / 10
    , 0)) AS violence_risk_score,
    CASE 
        WHEN COALESCE(vs.events_30d, 0) >= 500 THEN 'violence_crisis'
        WHEN COALESCE(vs.events_30d, 0) >= 100 THEN 'violence_high'
        WHEN COALESCE(vs.events_30d, 0) >= 20 THEN 'violence_watch'
        WHEN COALESCE(vs.events_30d, 0) > 0 THEN 'violence_low'
        ELSE 'no_data'
    END AS violence_tier,
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
'Violence risk proxy (ACLED). Uses week_start for aligned filtering. data_scope=proxy_general_violence.';
