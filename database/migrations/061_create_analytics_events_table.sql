-- ============================================================================
-- Migration 061: Create GA4 Analytics Events Table
-- Date: 2026-01-23
-- Purpose: Store Google Analytics 4 events from BigQuery export
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CREATE ANALYTICS EVENTS TABLE
-- ============================================================================

DROP TABLE IF EXISTS sofia.analytics_events CASCADE;

CREATE TABLE sofia.analytics_events (
    id BIGSERIAL PRIMARY KEY,

    -- Deduplication key (deterministic hash)
    event_hash TEXT NOT NULL UNIQUE,

    -- Event identification
    event_date DATE NOT NULL,
    event_timestamp BIGINT NOT NULL,
    event_name TEXT NOT NULL,

    -- User identification
    user_pseudo_id TEXT NOT NULL,
    ga_session_id BIGINT,

    -- Page information
    page_location TEXT,
    page_path TEXT,
    page_title TEXT,

    -- Traffic source
    source TEXT,
    medium TEXT,

    -- Device and geo
    device_category TEXT,
    country TEXT,

    -- Engagement metrics
    engagement_time_ms INTEGER,

    -- Metadata
    source_system TEXT NOT NULL DEFAULT 'GA4',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. CREATE INDEXES
-- ============================================================================

-- Performance indexes for common queries
CREATE INDEX idx_analytics_events_date ON sofia.analytics_events(event_date DESC);
CREATE INDEX idx_analytics_events_name ON sofia.analytics_events(event_name);
CREATE INDEX idx_analytics_events_page_path ON sofia.analytics_events(page_path);
CREATE INDEX idx_analytics_events_source_medium ON sofia.analytics_events(source, medium) WHERE source IS NOT NULL;
CREATE INDEX idx_analytics_events_user ON sofia.analytics_events(user_pseudo_id);
CREATE INDEX idx_analytics_events_session ON sofia.analytics_events(ga_session_id) WHERE ga_session_id IS NOT NULL;
CREATE INDEX idx_analytics_events_country ON sofia.analytics_events(country) WHERE country IS NOT NULL;
CREATE INDEX idx_analytics_events_device ON sofia.analytics_events(device_category) WHERE device_category IS NOT NULL;

-- Timestamp index for incremental queries
CREATE INDEX idx_analytics_events_timestamp ON sofia.analytics_events(event_timestamp DESC);
CREATE INDEX idx_analytics_events_ingested ON sofia.analytics_events(ingested_at DESC);

-- ============================================================================
-- 3. COMMENTS
-- ============================================================================

COMMENT ON TABLE sofia.analytics_events IS 'GA4 events from BigQuery export (production-grade collection)';
COMMENT ON COLUMN sofia.analytics_events.event_hash IS 'SHA256 hash for deduplication (event_date + event_timestamp + event_name + user_pseudo_id + page_location + ga_session_id)';
COMMENT ON COLUMN sofia.analytics_events.event_timestamp IS 'UNIX timestamp in microseconds (GA4 format)';
COMMENT ON COLUMN sofia.analytics_events.user_pseudo_id IS 'GA4 cookie-based user identifier';
COMMENT ON COLUMN sofia.analytics_events.ga_session_id IS 'GA4 session identifier';
COMMENT ON COLUMN sofia.analytics_events.page_path IS 'Normalized URL path (derived from page_location)';
COMMENT ON COLUMN sofia.analytics_events.engagement_time_ms IS 'User engagement time in milliseconds';
COMMENT ON COLUMN sofia.analytics_events.source_system IS 'Always GA4 for this table';

-- ============================================================================
-- 4. HELPER FUNCTION: Normalize URL to path
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.normalize_url_to_path(url TEXT)
RETURNS TEXT AS $$
DECLARE
    path_only TEXT;
BEGIN
    -- Return NULL if input is NULL
    IF url IS NULL THEN
        RETURN NULL;
    END IF;

    -- Extract path from URL (remove protocol, domain, query params, and fragments)
    -- Example: https://example.com/page?foo=bar#section -> /page

    -- Remove protocol (http://, https://)
    url := REGEXP_REPLACE(url, '^https?://', '');

    -- Remove domain (everything before first slash)
    url := REGEXP_REPLACE(url, '^[^/]+', '');

    -- If no slash found, return root
    IF url = '' OR url IS NULL THEN
        RETURN '/';
    END IF;

    -- Remove query string (everything after ?)
    url := REGEXP_REPLACE(url, '\?.*$', '');

    -- Remove fragment (everything after #)
    url := REGEXP_REPLACE(url, '#.*$', '');

    -- Ensure starts with /
    IF NOT url LIKE '/%' THEN
        url := '/' || url;
    END IF;

    RETURN url;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION sofia.normalize_url_to_path IS 'Extracts path from full URL for analytics_events.page_path';

-- ============================================================================
-- 5. VERIFICATION QUERY
-- ============================================================================

SELECT
    'Migration 061 Complete' as status,
    'Created sofia.analytics_events table for GA4 events' as message;

-- Summary query (will be empty initially)
SELECT
    'Analytics Events Summary' as report,
    COUNT(*) as total_events,
    COUNT(DISTINCT event_date) as unique_dates,
    COUNT(DISTINCT user_pseudo_id) as unique_users,
    MIN(event_date) as earliest_date,
    MAX(event_date) as latest_date
FROM sofia.analytics_events;

COMMIT;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Insert event with hash calculation
-- INSERT INTO sofia.analytics_events (
--     event_hash,
--     event_date,
--     event_timestamp,
--     event_name,
--     user_pseudo_id,
--     page_location,
--     page_path
-- ) VALUES (
--     encode(sha256(('20260123' || '1737598800000000' || 'page_view' || 'user123' || 'https://example.com/page' || '456')::bytea), 'hex'),
--     '2026-01-23',
--     1737598800000000,
--     'page_view',
--     'user123',
--     'https://example.com/page',
--     sofia.normalize_url_to_path('https://example.com/page')
-- ) ON CONFLICT (event_hash) DO NOTHING;

-- Example 2: Query daily page views
-- SELECT
--     event_date,
--     COUNT(*) as page_views,
--     COUNT(DISTINCT user_pseudo_id) as unique_users
-- FROM sofia.analytics_events
-- WHERE event_name = 'page_view'
--     AND event_date >= CURRENT_DATE - INTERVAL '7 days'
-- GROUP BY event_date
-- ORDER BY event_date DESC;

-- Example 3: Top pages
-- SELECT
--     page_path,
--     COUNT(*) as views,
--     COUNT(DISTINCT user_pseudo_id) as unique_users
-- FROM sofia.analytics_events
-- WHERE event_name = 'page_view'
--     AND event_date >= CURRENT_DATE - INTERVAL '30 days'
-- GROUP BY page_path
-- ORDER BY views DESC
-- LIMIT 20;
