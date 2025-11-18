-- Migration: Create IPO Calendar Table
-- Author: Sofia Pulse
-- Date: 2025-11-18
-- Description: Tabela para rastrear IPOs pendentes (NASDAQ, B3, etc)

CREATE TABLE IF NOT EXISTS sofia.ipo_calendar (
  id SERIAL PRIMARY KEY,
  company VARCHAR(255) NOT NULL,
  ticker VARCHAR(20),
  exchange VARCHAR(50) NOT NULL, -- 'NASDAQ', 'B3', 'NYSE', etc
  expected_date DATE,
  price_range VARCHAR(50), -- Ex: "$15-17"
  shares_offered BIGINT,
  market_cap BIGINT,
  sector VARCHAR(100),
  country VARCHAR(100) NOT NULL,
  underwriters TEXT[], -- Array de underwriters
  description TEXT,
  status VARCHAR(50) DEFAULT 'Expected', -- 'Expected', 'Filed', 'Priced', 'Trading', 'Withdrawn'
  filing_date DATE,
  source VARCHAR(100), -- 'nasdaq.com', 'b3.com.br', 'sec.gov'

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(company, exchange, expected_date)
);

-- Indexes
CREATE INDEX idx_ipo_exchange ON sofia.ipo_calendar(exchange);
CREATE INDEX idx_ipo_expected_date ON sofia.ipo_calendar(expected_date);
CREATE INDEX idx_ipo_country ON sofia.ipo_calendar(country);
CREATE INDEX idx_ipo_sector ON sofia.ipo_calendar(sector);
CREATE INDEX idx_ipo_status ON sofia.ipo_calendar(status);

-- Comments
COMMENT ON TABLE sofia.ipo_calendar IS 'IPOs pendentes e futuros das principais bolsas';
COMMENT ON COLUMN sofia.ipo_calendar.price_range IS 'Faixa de preço estimada (ex: "$15-17")';
COMMENT ON COLUMN sofia.ipo_calendar.status IS 'Expected: aguardando | Filed: S-1 filed | Priced: preço definido | Trading: já negociando';
COMMENT ON COLUMN sofia.ipo_calendar.underwriters IS 'Bancos underwriters (Goldman, Morgan Stanley, etc)';

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_ipo_calendar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ipo_calendar_updated_at
  BEFORE UPDATE ON sofia.ipo_calendar
  FOR EACH ROW
  EXECUTE FUNCTION update_ipo_calendar_updated_at();

-- Queries úteis

-- IPOs esperados nos próximos 30 dias
COMMENT ON TABLE sofia.ipo_calendar IS '
Query: IPOs nos próximos 30 dias
SELECT company, ticker, exchange, expected_date, price_range, sector
FROM sofia.ipo_calendar
WHERE expected_date BETWEEN NOW() AND NOW() + INTERVAL ''30 days''
  AND status IN (''Expected'', ''Filed'', ''Priced'')
ORDER BY expected_date;
';

-- Top setores com IPOs pendentes
COMMENT ON COLUMN sofia.ipo_calendar.sector IS '
Query: Setores com mais IPOs
SELECT sector, COUNT(*) as ipo_count,
  SUM(shares_offered * CAST(SPLIT_PART(price_range, ''-'', 2) AS DECIMAL)) as estimated_raise
FROM sofia.ipo_calendar
WHERE status IN (''Expected'', ''Filed'', ''Priced'')
  AND sector IS NOT NULL
GROUP BY sector
ORDER BY ipo_count DESC;
';
