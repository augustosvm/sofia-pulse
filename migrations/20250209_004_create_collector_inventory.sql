CREATE TABLE IF NOT EXISTS sofia.collector_inventory (
    collector_id VARCHAR(100) PRIMARY KEY,
    path TEXT NOT NULL, language VARCHAR(10) DEFAULT 'python',
    schedule VARCHAR(20) DEFAULT 'manual',
    enabled BOOLEAN DEFAULT TRUE, expected_min_records INTEGER DEFAULT 1,
    owner VARCHAR(50) DEFAULT 'sofia', tags TEXT[] DEFAULT '{}',
    depends_on TEXT[] DEFAULT '{}', output_tables TEXT[] DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'experimental',
    description TEXT, last_validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_inv_status ON sofia.collector_inventory(status);

CREATE OR REPLACE VIEW sofia.v_missing_runs_today AS
SELECT ci.collector_id, ci.path, ci.schedule, ci.expected_min_records
FROM sofia.collector_inventory ci
LEFT JOIN LATERAL (
    SELECT MAX(started_at) AS last_run
    FROM sofia.collector_runs WHERE collector_name = ci.collector_id AND started_at >= CURRENT_DATE
) cr ON TRUE
WHERE ci.enabled AND ci.schedule = 'daily' AND cr.last_run IS NULL;
