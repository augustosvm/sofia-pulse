CREATE TABLE IF NOT EXISTS sofia.budget_limits (
    scope VARCHAR(20) NOT NULL, scope_id VARCHAR(100) NOT NULL,
    limit_cost NUMERIC(10,4) DEFAULT 10.00, currency VARCHAR(3) DEFAULT 'USD',
    active BOOLEAN DEFAULT TRUE, created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (scope, scope_id)
);
CREATE TABLE IF NOT EXISTS sofia.budget_usage (
    id SERIAL PRIMARY KEY, scope VARCHAR(20) NOT NULL, scope_id VARCHAR(100) NOT NULL,
    trace_id UUID NOT NULL, skill VARCHAR(100), provider VARCHAR(50),
    cost NUMERIC(10,6) NOT NULL, tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0,
    requests INTEGER DEFAULT 1, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_bu_scope ON sofia.budget_usage(scope, scope_id, created_at);
INSERT INTO sofia.budget_limits VALUES ('day','global',5.00,'USD',true,NOW()) ON CONFLICT DO NOTHING;
