-- ============================================================================
-- UNIVERSAL CHANGESETS - Delta Tracking & Time-Travel
-- ============================================================================
-- Purpose: Track all data changes across Sofia Pulse for:
--   - Time-travel queries (see data as it was on any date)
--   - Undo operations
--   - Delta-based forecasting (trend analysis)
--   - Audit trail (who changed what when)
--   - Version diffs (compare states)
-- ============================================================================

-- Create operation types enum
CREATE TYPE sofia.changeset_operation AS ENUM (
    'INSERT',           -- New record created
    'UPDATE',           -- Existing record modified
    'DELETE',           -- Record deleted
    'TRUNCATE',         -- Table truncated
    'REFRESH'           -- Full data refresh
);

-- Main changesets table
CREATE TABLE IF NOT EXISTS sofia.changesets (
    id BIGSERIAL PRIMARY KEY,

    -- Source identification
    source_name TEXT NOT NULL,              -- Data source (e.g., 'github', 'world_bank', 'arxiv')
    source_table TEXT NOT NULL,             -- Table name in sofia schema
    source_pk TEXT NOT NULL,                -- Primary key value (as TEXT for flexibility)

    -- Operation
    operation sofia.changeset_operation NOT NULL,

    -- Delta payload
    payload_before JSONB,                   -- State before change (NULL for INSERT)
    payload_after JSONB,                    -- State after change (NULL for DELETE)
    delta JSONB GENERATED ALWAYS AS (
        CASE
            WHEN operation = 'INSERT' THEN payload_after
            WHEN operation = 'DELETE' THEN payload_before
            WHEN operation = 'UPDATE' THEN jsonb_build_object(
                'added', payload_after - payload_before,
                'removed', payload_before - payload_after,
                'changed', payload_after
            )
            ELSE NULL
        END
    ) STORED,                               -- Computed delta

    -- Metadata
    changed_columns TEXT[],                 -- List of columns that changed (for UPDATE)
    change_magnitude FLOAT,                 -- Magnitude of change (for forecasting)

    -- Provenance
    collector_run_id INTEGER,               -- Link to collector_runs table
    user_id TEXT,                           -- Who made the change (NULL for automated)

    -- Timestamps
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes will be created below
    CONSTRAINT valid_magnitude CHECK (change_magnitude IS NULL OR change_magnitude >= 0)
);

-- Create indexes for fast querying
CREATE INDEX idx_changesets_source ON sofia.changesets(source_name, source_table);
CREATE INDEX idx_changesets_source_pk ON sofia.changesets(source_pk);
CREATE INDEX idx_changesets_operation ON sofia.changesets(operation);
CREATE INDEX idx_changesets_collected_at ON sofia.changesets(collected_at DESC);
CREATE INDEX idx_changesets_created_at ON sofia.changesets(created_at DESC);
CREATE INDEX idx_changesets_collector_run ON sofia.changesets(collector_run_id);

-- GIN indexes for JSONB queries
CREATE INDEX idx_changesets_payload_before ON sofia.changesets USING GIN(payload_before);
CREATE INDEX idx_changesets_payload_after ON sofia.changesets USING GIN(payload_after);
CREATE INDEX idx_changesets_delta ON sofia.changesets USING GIN(delta);

-- Partial indexes for specific operations
CREATE INDEX idx_changesets_inserts ON sofia.changesets(source_name, source_table, collected_at DESC)
    WHERE operation = 'INSERT';
CREATE INDEX idx_changesets_updates ON sofia.changesets(source_name, source_table, collected_at DESC)
    WHERE operation = 'UPDATE';
CREATE INDEX idx_changesets_deletes ON sofia.changesets(source_name, source_table, collected_at DESC)
    WHERE operation = 'DELETE';

COMMENT ON TABLE sofia.changesets IS 'Universal change tracking - enables time-travel queries and delta analysis';
COMMENT ON COLUMN sofia.changesets.delta IS 'Auto-computed delta: full payload for INSERT/DELETE, diff for UPDATE';
COMMENT ON COLUMN sofia.changesets.change_magnitude IS 'Magnitude of change for forecasting (e.g., % change in value)';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to track a changeset
CREATE OR REPLACE FUNCTION sofia.track_changeset(
    p_source_name TEXT,
    p_source_table TEXT,
    p_source_pk TEXT,
    p_operation TEXT,
    p_payload_before JSONB DEFAULT NULL,
    p_payload_after JSONB DEFAULT NULL,
    p_changed_columns TEXT[] DEFAULT NULL,
    p_change_magnitude FLOAT DEFAULT NULL,
    p_collector_run_id INTEGER DEFAULT NULL,
    p_user_id TEXT DEFAULT NULL,
    p_collected_at TIMESTAMP DEFAULT NOW()
)
RETURNS BIGINT AS $$
DECLARE
    v_changeset_id BIGINT;
BEGIN
    INSERT INTO sofia.changesets (
        source_name,
        source_table,
        source_pk,
        operation,
        payload_before,
        payload_after,
        changed_columns,
        change_magnitude,
        collector_run_id,
        user_id,
        collected_at
    ) VALUES (
        p_source_name,
        p_source_table,
        p_source_pk,
        p_operation::sofia.changeset_operation,
        p_payload_before,
        p_payload_after,
        p_changed_columns,
        p_change_magnitude,
        p_collector_run_id,
        p_user_id,
        p_collected_at
    )
    RETURNING id INTO v_changeset_id;

    RETURN v_changeset_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.track_changeset IS 'Track a change to any data source - creates changeset record';

-- Function to get state at a point in time (time-travel)
CREATE OR REPLACE FUNCTION sofia.get_state_at_time(
    p_source_name TEXT,
    p_source_table TEXT,
    p_source_pk TEXT,
    p_timestamp TIMESTAMP
)
RETURNS JSONB AS $$
DECLARE
    v_state JSONB;
BEGIN
    -- Get the most recent changeset before or at the timestamp
    SELECT
        CASE
            WHEN operation = 'DELETE' THEN NULL
            ELSE payload_after
        END INTO v_state
    FROM sofia.changesets
    WHERE source_name = p_source_name
      AND source_table = p_source_table
      AND source_pk = p_source_pk
      AND collected_at <= p_timestamp
    ORDER BY collected_at DESC
    LIMIT 1;

    RETURN v_state;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.get_state_at_time IS 'Time-travel: get state of a record as it was at a specific timestamp';

-- Function to get all changes for a record
CREATE OR REPLACE FUNCTION sofia.get_change_history(
    p_source_name TEXT,
    p_source_table TEXT,
    p_source_pk TEXT,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    id BIGINT,
    operation sofia.changeset_operation,
    payload_before JSONB,
    payload_after JSONB,
    delta JSONB,
    changed_columns TEXT[],
    collected_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.operation,
        c.payload_before,
        c.payload_after,
        c.delta,
        c.changed_columns,
        c.collected_at
    FROM sofia.changesets c
    WHERE c.source_name = p_source_name
      AND c.source_table = p_source_table
      AND c.source_pk = p_source_pk
    ORDER BY c.collected_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.get_change_history IS 'Get complete change history for a specific record';

-- Function to get delta summary between two timestamps
CREATE OR REPLACE FUNCTION sofia.get_delta_summary(
    p_source_name TEXT,
    p_source_table TEXT,
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP
)
RETURNS TABLE (
    operation sofia.changeset_operation,
    count BIGINT,
    avg_magnitude FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.operation,
        COUNT(*) as count,
        AVG(c.change_magnitude) as avg_magnitude
    FROM sofia.changesets c
    WHERE c.source_name = p_source_name
      AND c.source_table = p_source_table
      AND c.collected_at >= p_start_time
      AND c.collected_at < p_end_time
    GROUP BY c.operation;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.get_delta_summary IS 'Get summary of changes between two timestamps';

-- Function to undo last change to a record
CREATE OR REPLACE FUNCTION sofia.undo_last_change(
    p_source_name TEXT,
    p_source_table TEXT,
    p_source_pk TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_last_change RECORD;
    v_undo_state JSONB;
BEGIN
    -- Get last change
    SELECT * INTO v_last_change
    FROM sofia.changesets
    WHERE source_name = p_source_name
      AND source_table = p_source_table
      AND source_pk = p_source_pk
    ORDER BY collected_at DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No changes found for this record';
    END IF;

    -- Determine undo state
    CASE v_last_change.operation
        WHEN 'INSERT' THEN
            -- Undo INSERT = DELETE
            v_undo_state := NULL;
        WHEN 'UPDATE' THEN
            -- Undo UPDATE = restore previous state
            v_undo_state := v_last_change.payload_before;
        WHEN 'DELETE' THEN
            -- Undo DELETE = restore deleted state
            v_undo_state := v_last_change.payload_before;
        ELSE
            RAISE EXCEPTION 'Cannot undo operation: %', v_last_change.operation;
    END CASE;

    RETURN v_undo_state;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.undo_last_change IS 'Undo last change to a record - returns state to restore (or NULL to delete)';

-- ============================================================================
-- AUTOMATIC CHANGE TRACKING (TRIGGERS)
-- ============================================================================

-- Generic trigger function to track changes
CREATE OR REPLACE FUNCTION sofia.changeset_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_source_name TEXT;
    v_source_table TEXT;
    v_source_pk TEXT;
    v_operation TEXT;
    v_payload_before JSONB;
    v_payload_after JSONB;
    v_changed_columns TEXT[];
BEGIN
    -- Extract source info
    v_source_name := TG_ARGV[0];  -- Pass as trigger argument
    v_source_table := TG_TABLE_NAME;

    -- Determine operation
    IF (TG_OP = 'INSERT') THEN
        v_operation := 'INSERT';
        v_source_pk := (NEW.id)::TEXT;
        v_payload_before := NULL;
        v_payload_after := to_jsonb(NEW);

    ELSIF (TG_OP = 'UPDATE') THEN
        v_operation := 'UPDATE';
        v_source_pk := (NEW.id)::TEXT;
        v_payload_before := to_jsonb(OLD);
        v_payload_after := to_jsonb(NEW);

        -- Detect changed columns
        v_changed_columns := ARRAY(
            SELECT jsonb_object_keys(v_payload_after - v_payload_before)
        );

    ELSIF (TG_OP = 'DELETE') THEN
        v_operation := 'DELETE';
        v_source_pk := (OLD.id)::TEXT;
        v_payload_before := to_jsonb(OLD);
        v_payload_after := NULL;

    ELSE
        RETURN NULL;
    END IF;

    -- Track the changeset
    PERFORM sofia.track_changeset(
        v_source_name,
        v_source_table,
        v_source_pk,
        v_operation,
        v_payload_before,
        v_payload_after,
        v_changed_columns
    );

    -- Return appropriate value
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.changeset_trigger IS 'Generic trigger function to automatically track changesets';

-- ============================================================================
-- EXAMPLE: Enable tracking for github_trending
-- ============================================================================

-- Uncomment to enable automatic tracking for github_trending:
-- CREATE TRIGGER track_github_trending_changes
--     AFTER INSERT OR UPDATE OR DELETE ON sofia.github_trending
--     FOR EACH ROW EXECUTE FUNCTION sofia.changeset_trigger('github');

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- View: Recent changes (last 24h)
CREATE OR REPLACE VIEW sofia.recent_changes AS
SELECT
    source_name,
    source_table,
    operation,
    COUNT(*) as change_count,
    MAX(collected_at) as last_change,
    AVG(change_magnitude) as avg_magnitude
FROM sofia.changesets
WHERE collected_at >= NOW() - INTERVAL '24 hours'
GROUP BY source_name, source_table, operation
ORDER BY last_change DESC;

-- View: Change velocity by source
CREATE OR REPLACE VIEW sofia.change_velocity AS
SELECT
    source_name,
    source_table,
    DATE_TRUNC('hour', collected_at) as hour,
    COUNT(*) as changes_per_hour,
    AVG(change_magnitude) as avg_magnitude
FROM sofia.changesets
WHERE collected_at >= NOW() - INTERVAL '7 days'
GROUP BY source_name, source_table, DATE_TRUNC('hour', collected_at)
ORDER BY hour DESC, changes_per_hour DESC;

-- View: Top modified records
CREATE OR REPLACE VIEW sofia.top_modified_records AS
SELECT
    source_name,
    source_table,
    source_pk,
    COUNT(*) as modification_count,
    MIN(collected_at) as first_modified,
    MAX(collected_at) as last_modified,
    COUNT(DISTINCT operation) as operation_types
FROM sofia.changesets
WHERE collected_at >= NOW() - INTERVAL '30 days'
GROUP BY source_name, source_table, source_pk
HAVING COUNT(*) > 1
ORDER BY modification_count DESC
LIMIT 100;

-- ============================================================================
-- RETENTION POLICY
-- ============================================================================

-- Function to archive old changesets (optional)
CREATE OR REPLACE FUNCTION sofia.archive_old_changesets(
    p_retention_days INTEGER DEFAULT 90
)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM sofia.changesets
    WHERE collected_at < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.archive_old_changesets IS 'Archive/delete changesets older than N days (default: 90)';

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT ON sofia.changesets TO PUBLIC;
GRANT SELECT ON sofia.recent_changes TO PUBLIC;
GRANT SELECT ON sofia.change_velocity TO PUBLIC;
GRANT SELECT ON sofia.top_modified_records TO PUBLIC;

-- ============================================================================
-- COMPLETE
-- ============================================================================

SELECT 'Universal Changesets system created successfully!' as status;
