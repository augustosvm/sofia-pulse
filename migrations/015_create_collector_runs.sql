-- ============================================================================
-- COLLECTOR RUNS TRACKING
-- ============================================================================
-- Registra TODA execução de TODOS os collectors.
-- Permite observabilidade total: quando rodou, quanto tempo, sucesso/erro, etc.
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.collector_runs (
    id SERIAL PRIMARY KEY,

    -- Identificação
    collector_name VARCHAR(100) NOT NULL,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    -- Valores: 'running', 'success', 'failed', 'timeout'

    -- Métricas
    items_collected INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,

    -- Error info
    error_message TEXT,
    error_stack TEXT,

    -- Metadata adicional
    metadata JSONB,
    -- Ex: { api_response_time: 1234, rate_limited: true, etc. }

    -- Ambiente
    hostname VARCHAR(255),
    -- Para saber qual servidor rodou (útil em multi-server)

    -- Constraints
    CHECK (status IN ('running', 'success', 'failed', 'timeout')),
    CHECK (items_collected >= 0),
    CHECK (items_failed >= 0)
);

-- Índices para queries rápidas
CREATE INDEX idx_collector_runs_name ON sofia.collector_runs(collector_name);
CREATE INDEX idx_collector_runs_started ON sofia.collector_runs(started_at DESC);
CREATE INDEX idx_collector_runs_status ON sofia.collector_runs(status);
CREATE INDEX idx_collector_runs_name_started ON sofia.collector_runs(collector_name, started_at DESC);

-- ============================================================================
-- VIEWS ÚTEIS
-- ============================================================================

-- Última execução de cada collector
CREATE OR REPLACE VIEW sofia.collector_last_run AS
SELECT DISTINCT ON (collector_name)
    collector_name,
    started_at as last_run_at,
    finished_at as last_finished_at,
    status as last_status,
    items_collected as last_items_collected,
    duration_ms as last_duration_ms,
    error_message as last_error
FROM sofia.collector_runs
ORDER BY collector_name, started_at DESC;

-- Estatísticas por collector
CREATE OR REPLACE VIEW sofia.collector_stats AS
SELECT
    collector_name,
    COUNT(*) as total_runs,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_runs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
    ROUND(100.0 * COUNT(CASE WHEN status = 'success' THEN 1 END) / COUNT(*), 2) as success_rate,
    MAX(started_at) as last_run_at,
    AVG(duration_ms) as avg_duration_ms,
    SUM(items_collected) as total_items_collected,
    SUM(items_failed) as total_items_failed
FROM sofia.collector_runs
GROUP BY collector_name
ORDER BY last_run_at DESC NULLS LAST;

-- Collectors que falharam recentemente
CREATE OR REPLACE VIEW sofia.collector_recent_failures AS
SELECT
    collector_name,
    started_at,
    error_message,
    items_collected,
    items_failed
FROM sofia.collector_runs
WHERE status = 'failed'
  AND started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC;

-- Collectors que não rodaram recentemente (possível problema)
CREATE OR REPLACE VIEW sofia.collector_stale AS
SELECT
    collector_name,
    MAX(started_at) as last_run_at,
    NOW() - MAX(started_at) as time_since_last_run
FROM sofia.collector_runs
GROUP BY collector_name
HAVING MAX(started_at) < NOW() - INTERVAL '2 days'
ORDER BY last_run_at DESC;

-- ============================================================================
-- FUNÇÕES ÚTEIS
-- ============================================================================

-- Iniciar tracking de uma execução
CREATE OR REPLACE FUNCTION sofia.start_collector_run(
    p_collector_name VARCHAR,
    p_hostname VARCHAR DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_run_id INTEGER;
BEGIN
    INSERT INTO sofia.collector_runs (
        collector_name,
        started_at,
        status,
        hostname
    ) VALUES (
        p_collector_name,
        NOW(),
        'running',
        p_hostname
    ) RETURNING id INTO v_run_id;

    RETURN v_run_id;
END;
$$ LANGUAGE plpgsql;

-- Finalizar tracking de uma execução
CREATE OR REPLACE FUNCTION sofia.finish_collector_run(
    p_run_id INTEGER,
    p_status VARCHAR,
    p_items_collected INTEGER DEFAULT 0,
    p_items_failed INTEGER DEFAULT 0,
    p_error_message TEXT DEFAULT NULL,
    p_error_stack TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE sofia.collector_runs
    SET
        finished_at = NOW(),
        duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000,
        status = p_status,
        items_collected = p_items_collected,
        items_failed = p_items_failed,
        error_message = p_error_message,
        error_stack = p_error_stack,
        metadata = p_metadata
    WHERE id = p_run_id;
END;
$$ LANGUAGE plpgsql;

-- Limpar runs antigas (manter últimos 30 dias)
CREATE OR REPLACE FUNCTION sofia.cleanup_old_collector_runs(
    p_days_to_keep INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM sofia.collector_runs
    WHERE started_at < NOW() - (p_days_to_keep || ' days')::INTERVAL;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON TABLE sofia.collector_runs IS 'Registra toda execução de collectors para observabilidade total';
COMMENT ON COLUMN sofia.collector_runs.collector_name IS 'Nome do collector (ex: github, npm, pypi)';
COMMENT ON COLUMN sofia.collector_runs.status IS 'Status: running, success, failed, timeout';
COMMENT ON COLUMN sofia.collector_runs.metadata IS 'Dados extras: API response time, rate limited, etc.';

COMMENT ON VIEW sofia.collector_last_run IS 'Última execução de cada collector';
COMMENT ON VIEW sofia.collector_stats IS 'Estatísticas agregadas por collector';
COMMENT ON VIEW sofia.collector_recent_failures IS 'Falhas dos últimos 7 dias';
COMMENT ON VIEW sofia.collector_stale IS 'Collectors que não rodaram há mais de 2 dias';
