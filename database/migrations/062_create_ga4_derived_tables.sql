-- ============================================================================
-- Migration 062: Create GA4 Derived Tables
-- Date: 2026-01-23
-- Purpose: Create derived tables for GA4 Intelligence V2.1
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CONTENT META TABLE (for deep read scoring)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.content_meta (
    page_path TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    author TEXT,
    publish_date DATE,
    word_count INTEGER NOT NULL,
    reading_time_sec INTEGER NOT NULL,
    last_scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_meta_word_count ON sofia.content_meta(word_count);
CREATE INDEX IF NOT EXISTS idx_content_meta_reading_time ON sofia.content_meta(reading_time_sec);
CREATE INDEX IF NOT EXISTS idx_content_meta_author ON sofia.content_meta(author) WHERE author IS NOT NULL;

COMMENT ON TABLE sofia.content_meta IS 'Content metadata for deep read scoring (word_count, reading_time)';
COMMENT ON COLUMN sofia.content_meta.reading_time_sec IS 'Estimated reading time: ceil((word_count / 200) * 60) seconds';

-- ============================================================================
-- 2. CHAT SESSIONS TABLE (derived from analytics_events)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.ga4_chat_sessions (
    conversation_key TEXT PRIMARY KEY,
    user_pseudo_id TEXT NOT NULL,
    ga_session_id BIGINT,
    entry_page_path TEXT,
    source TEXT,
    medium TEXT,
    device_category TEXT,
    country TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    user_messages_count INTEGER NOT NULL DEFAULT 0,
    user_chars_total INTEGER NOT NULL DEFAULT 0,
    sofia_responses_count INTEGER NOT NULL DEFAULT 0,
    first_response_latency_ms INTEGER,
    qualified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ga4_chat_sessions_user ON sofia.ga4_chat_sessions(user_pseudo_id);
CREATE INDEX idx_ga4_chat_sessions_page ON sofia.ga4_chat_sessions(entry_page_path);
CREATE INDEX idx_ga4_chat_sessions_source ON sofia.ga4_chat_sessions(source, medium);
CREATE INDEX idx_ga4_chat_sessions_qualified ON sofia.ga4_chat_sessions(qualified) WHERE qualified = TRUE;
CREATE INDEX idx_ga4_chat_sessions_started ON sofia.ga4_chat_sessions(started_at DESC);

COMMENT ON TABLE sofia.ga4_chat_sessions IS 'Derived chat sessions from analytics_events (real conversations only)';
COMMENT ON COLUMN sofia.ga4_chat_sessions.conversation_key IS 'Deterministic hash: md5(user_pseudo_id || ga_session_id || entry_page_path || date)';
COMMENT ON COLUMN sofia.ga4_chat_sessions.qualified IS 'TRUE if >= 3 messages OR >= 200 chars OR >= 120s interaction';

-- ============================================================================
-- 3. DAILY ROLLUPS TABLE (aggregated daily metrics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.ga4_daily_rollups (
    rollup_date DATE NOT NULL,
    source TEXT,
    medium TEXT,
    page_path TEXT,
    users INTEGER NOT NULL DEFAULT 0,
    pageviews INTEGER NOT NULL DEFAULT 0,
    engagement_time_total_sec INTEGER NOT NULL DEFAULT 0,
    deep_read_true_count INTEGER NOT NULL DEFAULT 0,
    deep_read_partial_count INTEGER NOT NULL DEFAULT 0,
    deep_read_score_avg NUMERIC(5,3),
    chat_conversations_started INTEGER NOT NULL DEFAULT 0,
    chat_conversations_qualified INTEGER NOT NULL DEFAULT 0,
    chat_user_messages_total INTEGER NOT NULL DEFAULT 0,
    return_users_7d_proxy INTEGER NOT NULL DEFAULT 0,
    is_proxy_flags JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (rollup_date, source, medium, page_path)
);

CREATE INDEX idx_ga4_daily_rollups_date ON sofia.ga4_daily_rollups(rollup_date DESC);
CREATE INDEX idx_ga4_daily_rollups_source ON sofia.ga4_daily_rollups(source, medium);
CREATE INDEX idx_ga4_daily_rollups_page ON sofia.ga4_daily_rollups(page_path);
CREATE INDEX idx_ga4_daily_rollups_deep_read ON sofia.ga4_daily_rollups(deep_read_score_avg DESC NULLS LAST);

COMMENT ON TABLE sofia.ga4_daily_rollups IS 'Daily aggregated GA4 metrics for fast reporting (180 days retention)';
COMMENT ON COLUMN sofia.ga4_daily_rollups.deep_read_score_avg IS 'Average deep read score: engagement_time_sec / reading_time_sec';
COMMENT ON COLUMN sofia.ga4_daily_rollups.is_proxy_flags IS 'Transparency flags for proxy metrics (e.g., deep_read_fallback)';

-- ============================================================================
-- 4. RETENTION COHORTS TABLE (weekly cohorts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.ga4_retention_cohorts (
    cohort_week TEXT PRIMARY KEY,  -- YYYY-WW format
    new_users INTEGER NOT NULL DEFAULT 0,
    returned_7d INTEGER NOT NULL DEFAULT 0,
    returned_28d INTEGER NOT NULL DEFAULT 0,
    returned_7d_rate NUMERIC(5,3),
    returned_28d_rate NUMERIC(5,3),
    new_users_chatters INTEGER NOT NULL DEFAULT 0,
    returned_7d_chatters INTEGER NOT NULL DEFAULT 0,
    returned_7d_rate_chatters NUMERIC(5,3),
    new_users_deep_readers INTEGER NOT NULL DEFAULT 0,
    returned_7d_deep_readers INTEGER NOT NULL DEFAULT 0,
    returned_7d_rate_deep_readers NUMERIC(5,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ga4_retention_cohorts_week ON sofia.ga4_retention_cohorts(cohort_week DESC);

COMMENT ON TABLE sofia.ga4_retention_cohorts IS 'Weekly cohort retention analysis (7d and 28d)';
COMMENT ON COLUMN sofia.ga4_retention_cohorts.cohort_week IS 'ISO week format: YYYY-WW (e.g., 2026-04)';

-- ============================================================================
-- 5. HELPER FUNCTIONS
-- ============================================================================

-- Function to generate conversation_key
CREATE OR REPLACE FUNCTION sofia.generate_conversation_key(
    p_user_pseudo_id TEXT,
    p_ga_session_id BIGINT,
    p_entry_page_path TEXT,
    p_event_date DATE
) RETURNS TEXT AS $$
BEGIN
    RETURN MD5(
        COALESCE(p_user_pseudo_id, '') || '|' ||
        COALESCE(p_ga_session_id::TEXT, '') || '|' ||
        COALESCE(p_entry_page_path, '') || '|' ||
        p_event_date::TEXT
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION sofia.generate_conversation_key IS 'Generate deterministic conversation key for chat sessions';

-- Function to calculate deep read score
CREATE OR REPLACE FUNCTION sofia.calculate_deep_read_score(
    p_engagement_time_ms INTEGER,
    p_reading_time_sec INTEGER
) RETURNS NUMERIC AS $$
DECLARE
    engagement_sec NUMERIC;
    score NUMERIC;
BEGIN
    IF p_reading_time_sec IS NULL OR p_reading_time_sec = 0 THEN
        RETURN NULL;
    END IF;

    engagement_sec := p_engagement_time_ms / 1000.0;
    score := LEAST(1.0, engagement_sec / p_reading_time_sec);

    RETURN ROUND(score, 3);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION sofia.calculate_deep_read_score IS 'Calculate deep read score: min(1.0, engagement_time_sec / reading_time_sec)';

-- ============================================================================
-- 6. VERIFICATION QUERY
-- ============================================================================

SELECT
    'Migration 062 Complete' as status,
    'Created GA4 derived tables: content_meta, ga4_chat_sessions, ga4_daily_rollups, ga4_retention_cohorts' as message;

-- Summary query
SELECT
    (SELECT COUNT(*) FROM sofia.content_meta) as content_meta_count,
    (SELECT COUNT(*) FROM sofia.ga4_chat_sessions) as chat_sessions_count,
    (SELECT COUNT(*) FROM sofia.ga4_daily_rollups) as daily_rollups_count,
    (SELECT COUNT(*) FROM sofia.ga4_retention_cohorts) as retention_cohorts_count;

COMMIT;

-- ============================================================================
-- USAGE NOTES
-- ============================================================================

-- To populate tables:
-- 1. Run analytics/content_meta_builder.py (weekly or when new pages appear)
-- 2. Run analytics/build_ga4_chat_sessions.py (daily, after GA4 collection)
-- 3. Run analytics/build_ga4_daily_rollups.py (daily, after chat sessions)
-- 4. Run analytics/build_ga4_retention_cohorts.py (weekly, on Sundays)

-- To query deep read with score:
-- SELECT
--     e.page_path,
--     AVG(sofia.calculate_deep_read_score(e.engagement_time_ms, cm.reading_time_sec)) as avg_deep_read_score
-- FROM sofia.analytics_events e
-- LEFT JOIN sofia.content_meta cm ON e.page_path = cm.page_path
-- WHERE e.event_name = 'page_view'
-- GROUP BY e.page_path;
