-- Migration: Capital Events (Capital & Financing Signals)
-- Substitui funding_rounds por dados governamentais reais
-- Fontes: SEC Form D (EUA), CVM Ofertas (BR), BNDES Desembolsos (BR)

-- Tabela principal canônica
CREATE TABLE IF NOT EXISTS capital_events (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- SEC_FORM_D | CVM_OFERTA | BNDES_DESEMBOLSO
    event_type VARCHAR(50) NOT NULL, -- PRIVATE_OFFERING | PUBLIC_OFFERING | DISBURSEMENT
    source_id VARCHAR(255) NOT NULL, -- ID original do dataset
    event_date DATE,
    country_code VARCHAR(3) DEFAULT 'USA',
    state_code VARCHAR(10),
    city VARCHAR(255),
    entity_name VARCHAR(500),
    amount DECIMAL(20, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    amount_usd DECIMAL(20, 2),
    sector VARCHAR(255),
    subsector VARCHAR(255),
    raw_payload JSONB,
    source_url TEXT,
    ingested_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_source_event UNIQUE (source, source_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_capital_events_source ON capital_events(source);
CREATE INDEX IF NOT EXISTS idx_capital_events_event_type ON capital_events(event_type);
CREATE INDEX IF NOT EXISTS idx_capital_events_event_date ON capital_events(event_date);
CREATE INDEX IF NOT EXISTS idx_capital_events_country ON capital_events(country_code);
CREATE INDEX IF NOT EXISTS idx_capital_events_state ON capital_events(state_code);
CREATE INDEX IF NOT EXISTS idx_capital_events_sector ON capital_events(sector);

-- Materialized View: Agregação mensal
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_capital_signals_monthly AS
SELECT
    DATE_TRUNC('month', event_date) AS month,
    source,
    event_type,
    country_code,
    COUNT(*) AS count_events,
    SUM(amount) AS sum_amount,
    SUM(amount_usd) AS sum_amount_usd,
    AVG(amount_usd) AS avg_amount_usd
FROM capital_events
WHERE event_date IS NOT NULL
GROUP BY DATE_TRUNC('month', event_date), source, event_type, country_code
ORDER BY month DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_capital_monthly
ON mv_capital_signals_monthly(month, source, event_type, country_code);

-- Materialized View: Agregação geográfica Brasil
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_capital_signals_geo_br AS
SELECT
    state_code,
    city,
    DATE_TRUNC('month', event_date) AS month,
    source,
    COUNT(*) AS count_events,
    SUM(amount) AS sum_amount,
    SUM(amount_usd) AS sum_amount_usd
FROM capital_events
WHERE country_code = 'BRA' AND event_date IS NOT NULL
GROUP BY state_code, city, DATE_TRUNC('month', event_date), source
ORDER BY sum_amount_usd DESC NULLS LAST;

CREATE INDEX IF NOT EXISTS idx_mv_capital_geo_br_state ON mv_capital_signals_geo_br(state_code);

-- Materialized View: Momentum (últimos 7/30 dias)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_capital_signals_momentum AS
WITH recent_data AS (
    SELECT
        source,
        event_type,
        country_code,
        COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '7 days') AS last_7_days_count,
        COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days') AS last_30_days_count,
        SUM(amount_usd) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '7 days') AS last_7_days_amount,
        SUM(amount_usd) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '30 days') AS last_30_days_amount,
        COUNT(*) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '60 days' AND event_date < CURRENT_DATE - INTERVAL '30 days') AS prev_30_days_count,
        SUM(amount_usd) FILTER (WHERE event_date >= CURRENT_DATE - INTERVAL '60 days' AND event_date < CURRENT_DATE - INTERVAL '30 days') AS prev_30_days_amount
    FROM capital_events
    GROUP BY source, event_type, country_code
)
SELECT
    source,
    event_type,
    country_code,
    last_7_days_count,
    last_30_days_count,
    last_7_days_amount,
    last_30_days_amount,
    CASE
        WHEN prev_30_days_count > 0 THEN
            ROUND(((last_30_days_count::DECIMAL - prev_30_days_count) / prev_30_days_count) * 100, 2)
        ELSE NULL
    END AS count_delta_percent,
    CASE
        WHEN prev_30_days_amount > 0 THEN
            ROUND(((last_30_days_amount - prev_30_days_amount) / prev_30_days_amount) * 100, 2)
        ELSE NULL
    END AS amount_delta_percent
FROM recent_data;

-- Materialized View: Top setores
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_capital_signals_by_sector AS
SELECT
    sector,
    source,
    country_code,
    COUNT(*) AS count_events,
    SUM(amount_usd) AS sum_amount_usd,
    AVG(amount_usd) AS avg_amount_usd,
    MAX(event_date) AS last_event_date
FROM capital_events
WHERE sector IS NOT NULL
GROUP BY sector, source, country_code
ORDER BY sum_amount_usd DESC NULLS LAST;

-- Função para refresh das views
CREATE OR REPLACE FUNCTION refresh_capital_views() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_capital_signals_monthly;
    REFRESH MATERIALIZED VIEW mv_capital_signals_geo_br;
    REFRESH MATERIALIZED VIEW mv_capital_signals_momentum;
    REFRESH MATERIALIZED VIEW mv_capital_signals_by_sector;
END;
$$ LANGUAGE plpgsql;

-- Comentários para documentação
COMMENT ON TABLE capital_events IS 'Eventos de capital de fontes governamentais oficiais (SEC, CVM, BNDES)';
COMMENT ON COLUMN capital_events.source IS 'Fonte: SEC_FORM_D, CVM_OFERTA, BNDES_DESEMBOLSO';
COMMENT ON COLUMN capital_events.event_type IS 'Tipo: PRIVATE_OFFERING, PUBLIC_OFFERING, DISBURSEMENT';
