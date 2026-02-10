CREATE SCHEMA IF NOT EXISTS sofia;
CREATE TABLE IF NOT EXISTS sofia.collector_runs (
    run_id UUID PRIMARY KEY, trace_id UUID NOT NULL,
    collector_name VARCHAR(100) NOT NULL, collector_path TEXT NOT NULL,
    actor VARCHAR(20) DEFAULT 'system',
    started_at TIMESTAMPTZ DEFAULT NOW(), finished_at TIMESTAMPTZ,
    duration_ms INTEGER, fetched INTEGER DEFAULT 0, saved INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0, exit_code INTEGER, ok BOOLEAN DEFAULT FALSE,
    error_code VARCHAR(50), error_message TEXT, params JSONB,
    env VARCHAR(20) DEFAULT 'prod', created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cr_name ON sofia.collector_runs(collector_name);
CREATE INDEX IF NOT EXISTS idx_cr_trace ON sofia.collector_runs(trace_id);
CREATE INDEX IF NOT EXISTS idx_cr_date ON sofia.collector_runs(started_at DESC);
