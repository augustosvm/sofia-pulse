-- ============================================================================
-- SOFIA PULSE V2 — SCHEMA DEFINITION (PROD PROOF)
-- Strategy: Single Table + Semantic Metrics + Robust Constraints
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.collector_runs_v2 (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collector_id VARCHAR(100) NOT NULL,
    
    -- Execution Context
    command TEXT NOT NULL,
    hostname VARCHAR(100),
    pid INTEGER,
    
    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    
    -- Semantic Metrics
    items_read INTEGER DEFAULT 0,
    items_candidate INTEGER DEFAULT 0,
    items_inserted INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_ignored_conflict INTEGER DEFAULT 0,
    
    -- Impact & Audit
    tables_affected TEXT[] DEFAULT '{}',
    source VARCHAR(100), 
    
    -- Debugging
    error_message TEXT,
    exit_code INTEGER,
    full_log_path TEXT,
    stdout_tail TEXT,
    stderr_tail TEXT,
    meta JSONB DEFAULT '{}',
    
    -- CONSTRAINTS
    CONSTRAINT chk_runs_v2_status CHECK (status IN ('running', 'success', 'failed', 'zombie', 'invalid_output', 'timeout')),
    
    -- Source mandatory only on SUCCESS
    CONSTRAINT chk_runs_v2_source CHECK (
        status <> 'success' 
        OR (source IS NOT NULL AND length(source) > 0 AND source <> 'unknown')
    ),
    
    -- Non-negativity
    CONSTRAINT chk_runs_v2_metrics_nonneg CHECK (
        items_read >= 0 AND 
        items_candidate >= 0 AND
        items_inserted >= 0 AND 
        items_updated >= 0 AND 
        items_ignored_conflict >= 0 AND
        (duration_ms IS NULL OR duration_ms >= 0)
    )
);

-- Indexes (Safe Creation)
CREATE INDEX IF NOT EXISTS idx_runs_v2_lookup ON sofia.collector_runs_v2(collector_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_v2_status ON sofia.collector_runs_v2(status);
CREATE INDEX IF NOT EXISTS idx_runs_v2_started ON sofia.collector_runs_v2(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_v2_source_ts ON sofia.collector_runs_v2(source, started_at DESC);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- v_collector_health: Optimized (No SELECT *)
CREATE OR REPLACE VIEW sofia.v_collector_health AS
WITH last_runs AS (
    SELECT DISTINCT ON (collector_id) 
        collector_id, status, started_at, finished_at, 
        items_inserted, items_updated, error_message, meta
    FROM sofia.collector_runs_v2
    ORDER BY collector_id, started_at DESC
)
SELECT 
    lr.collector_id,
    lr.status as last_status,
    lr.started_at as last_run_at,
    CASE 
        WHEN lr.status = 'running' AND NOW() - lr.started_at > INTERVAL '1 hour' THEN 'zombie'
        WHEN lr.status = 'running' THEN 'running'
        -- Robust checking for allow_empty in meta JSONB (NULL-safe)
        WHEN lr.status = 'success' 
             AND (lr.items_inserted + lr.items_updated) = 0 
             AND COALESCE(lower(lr.meta->>'allow_empty'), '') NOT IN ('true', 't', '1', 'yes', 'y', 'on')
             THEN 'suspect_empty'
        WHEN lr.status = 'success' THEN 'healthy'
        ELSE 'error'
    END as health_state,
    (lr.items_inserted + lr.items_updated) as last_total_written,
    lr.error_message as last_error
FROM last_runs lr;

-- Other views (Explicit columns)
CREATE OR REPLACE VIEW sofia.v_collector_last_run AS
SELECT DISTINCT ON (collector_id)
    collector_id, status, source, started_at, finished_at,
    items_read, items_candidate, items_inserted, items_updated, items_ignored_conflict,
    (items_inserted + items_updated) AS total_written,
    error_message, exit_code, full_log_path, stdout_tail, stderr_tail, meta
FROM sofia.collector_runs_v2
ORDER BY collector_id, started_at DESC;

CREATE OR REPLACE VIEW sofia.v_collector_weekly_stats AS
SELECT 
    collector_id,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (WHERE status='success') AS success_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status='success') / NULLIF(COUNT(*),0), 1) AS success_rate,
    SUM(items_inserted) AS total_inserts,
    SUM(items_updated) AS total_updates,
    SUM(items_ignored_conflict) AS total_ignored,
    MAX(started_at) AS last_seen
FROM sofia.collector_runs_v2
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY collector_id;
