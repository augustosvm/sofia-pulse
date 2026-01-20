-- ============================================================================
-- Migration 017d: Week Start Standardization (All Temporal Tables)
-- Purpose: Extend week_start pattern to all tables with weekly buckets
-- Based on discovery: security_events.week_start needs alignment fix
-- ============================================================================

-- ============================================================================
-- TABLE: security_events
-- Column: week_start (already exists but misaligned)
-- ============================================================================

-- Fix misaligned week_start values in security_events
UPDATE sofia.security_events 
SET week_start = date_trunc('week', week_start)::date 
WHERE week_start <> date_trunc('week', week_start);

-- Create index for performance (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'sofia' 
          AND tablename = 'security_events' 
          AND indexname = 'idx_security_events_week_start'
    ) THEN
        CREATE INDEX idx_security_events_week_start 
        ON sofia.security_events(week_start);
        
        RAISE NOTICE 'Created index on security_events.week_start';
    ELSE
        RAISE NOTICE 'Index idx_security_events_week_start already exists';
    END IF;
END $$;

-- Create composite index for common query pattern
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'sofia' 
          AND tablename = 'security_events' 
          AND indexname = 'idx_security_events_country_week_start'
    ) THEN
        -- Check if country_id or country_code column exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'sofia' 
              AND table_name = 'security_events'
              AND column_name IN ('country_id', 'country_code')
        ) THEN
            -- Use whichever column exists
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'sofia' 
                  AND table_name = 'security_events' 
                  AND column_name = 'country_id'
            ) THEN
                CREATE INDEX idx_security_events_country_week_start 
                ON sofia.security_events(country_id, week_start);
                RAISE NOTICE 'Created composite index on country_id, week_start';
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'sofia' 
                  AND table_name = 'security_events' 
                  AND column_name = 'country_code'
            ) THEN
                CREATE INDEX idx_security_events_country_week_start 
                ON sofia.security_events(country_code, week_start);
                RAISE NOTICE 'Created composite index on country_code, week_start';
            END IF;
        END IF;
    ELSE
        RAISE NOTICE 'Composite index already exists';
    END IF;
END $$;

COMMENT ON COLUMN sofia.security_events.week_start IS 
'Week-aligned date (Monday) for deterministic time window filtering. Always date_trunc(week, original_date)::date';

-- ============================================================================
-- Data Quality Health Check View
-- ============================================================================

CREATE OR REPLACE VIEW sofia.v_data_quality_week_alignment AS
WITH table_checks AS (
    -- acled_aggregated.week
    SELECT 
        'acled_aggregated'::text AS table_name,
        'week'::text AS column_name,
        COUNT(*) AS total_rows,
        COUNT(DISTINCT week) AS distinct_weeks,
        COUNT(*) FILTER (WHERE week <> date_trunc('week', week)) AS rows_not_aligned,
        COUNT(DISTINCT week) FILTER (WHERE week <> date_trunc('week', week)) AS distinct_weeks_not_aligned
    FROM sofia.acled_aggregated
    WHERE week IS NOT NULL
    
    UNION ALL
    
    -- acled_aggregated.week_start (should be perfect after 017c)
    SELECT 
        'acled_aggregated'::text,
        'week_start'::text,
        COUNT(*),
        COUNT(DISTINCT week_start),
        COUNT(*) FILTER (WHERE week_start <> date_trunc('week', week_start)),
        COUNT(DISTINCT week_start) FILTER (WHERE week_start <> date_trunc('week', week_start))
    FROM sofia.acled_aggregated
    WHERE week_start IS NOT NULL
    
    UNION ALL
    
    -- security_events.week_start
    SELECT 
        'security_events'::text,
        'week_start'::text,
        COUNT(*),
        COUNT(DISTINCT week_start),
        COUNT(*) FILTER (WHERE week_start <> date_trunc('week', week_start)),
        COUNT(DISTINCT week_start) FILTER (WHERE week_start <> date_trunc('week', week_start))
    FROM sofia.security_events
    WHERE week_start IS NOT NULL
)
SELECT 
    table_name,
    column_name,
    total_rows,
    distinct_weeks,
    rows_not_aligned,
    distinct_weeks_not_aligned,
    ROUND((rows_not_aligned::numeric / NULLIF(total_rows, 0)) * 100, 2) AS pct_rows_not_aligned,
    ROUND((distinct_weeks_not_aligned::numeric / NULLIF(distinct_weeks, 0)) * 100, 2) AS pct_distinct_not_aligned,
    CASE 
        WHEN distinct_weeks_not_aligned = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM table_checks
ORDER BY distinct_weeks_not_aligned DESC, table_name, column_name;

COMMENT ON VIEW sofia.v_data_quality_week_alignment IS
'Enterprise health check for week alignment across temporal tables. Returns PASS if all weeks are Monday-aligned.';
