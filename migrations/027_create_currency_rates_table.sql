-- Migration 027: Create Currency Rates Table
-- Created: 2025-12-24
-- Purpose: Store historical exchange rates for multi-currency data normalization

-- ============================================================================
-- CURRENCY RATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.currency_rates (
  id SERIAL PRIMARY KEY,

  -- Currency info
  currency_code VARCHAR(3) NOT NULL,     -- ISO 4217: USD, EUR, BRL, etc.
  currency_name VARCHAR(50),             -- Full name: US Dollar, Euro, Brazilian Real

  -- Exchange rates (all relative to USD)
  rate_to_usd NUMERIC(12, 6) NOT NULL,   -- 1 BRL = 0.20 USD
  rate_from_usd NUMERIC(12, 6) NOT NULL, -- 1 USD = 5.00 BRL

  -- Metadata
  source VARCHAR(50) DEFAULT 'exchangerate-api',
  fetched_at TIMESTAMP DEFAULT NOW(),
  valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
  valid_until DATE,

  -- Constraints
  CONSTRAINT currency_rates_unique_daily UNIQUE (currency_code, valid_from),
  CONSTRAINT currency_rates_positive_rate CHECK (rate_to_usd > 0 AND rate_from_usd > 0)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_currency_rates_code ON sofia.currency_rates(currency_code);
CREATE INDEX IF NOT EXISTS idx_currency_rates_date ON sofia.currency_rates(valid_from DESC);
CREATE INDEX IF NOT EXISTS idx_currency_rates_code_date ON sofia.currency_rates(currency_code, valid_from DESC);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE sofia.currency_rates IS 'Historical exchange rates for currency normalization across all data sources';
COMMENT ON COLUMN sofia.currency_rates.rate_to_usd IS 'How much USD 1 unit of this currency equals (e.g., 1 BRL = 0.20 USD)';
COMMENT ON COLUMN sofia.currency_rates.rate_from_usd IS 'How much of this currency 1 USD equals (e.g., 1 USD = 5.00 BRL)';
COMMENT ON COLUMN sofia.currency_rates.valid_from IS 'Date this rate became effective';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get latest exchange rate for a currency
CREATE OR REPLACE FUNCTION sofia.get_exchange_rate(
    p_currency_code VARCHAR,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS NUMERIC AS $$
DECLARE
    v_rate NUMERIC;
BEGIN
    -- Return 1.0 for USD (base currency)
    IF UPPER(p_currency_code) = 'USD' THEN
        RETURN 1.0;
    END IF;

    -- Get rate for specific date (or latest before that date)
    SELECT rate_to_usd INTO v_rate
    FROM sofia.currency_rates
    WHERE currency_code = UPPER(p_currency_code)
      AND valid_from <= p_date
    ORDER BY valid_from DESC
    LIMIT 1;

    -- Return rate or NULL if not found
    RETURN v_rate;
END;
$$ LANGUAGE plpgsql STABLE;

-- Convert amount from one currency to another
CREATE OR REPLACE FUNCTION sofia.convert_currency(
    p_amount NUMERIC,
    p_from_currency VARCHAR,
    p_to_currency VARCHAR DEFAULT 'USD',
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS NUMERIC AS $$
DECLARE
    v_from_rate NUMERIC;
    v_to_rate NUMERIC;
    v_result NUMERIC;
BEGIN
    -- Handle NULL amount
    IF p_amount IS NULL THEN
        RETURN NULL;
    END IF;

    -- Same currency, no conversion needed
    IF UPPER(p_from_currency) = UPPER(p_to_currency) THEN
        RETURN p_amount;
    END IF;

    -- Get rates
    v_from_rate := sofia.get_exchange_rate(p_from_currency, p_date);
    v_to_rate := sofia.get_exchange_rate(p_to_currency, p_date);

    -- Check if rates exist
    IF v_from_rate IS NULL OR v_to_rate IS NULL THEN
        RETURN NULL;
    END IF;

    -- Convert: amount -> USD -> target currency
    v_result := (p_amount * v_from_rate) / v_to_rate;

    RETURN ROUND(v_result, 2);
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- SEED DATA (Initial rates - will be updated daily by collector)
-- ============================================================================

INSERT INTO sofia.currency_rates (currency_code, currency_name, rate_to_usd, rate_from_usd, source, valid_from)
VALUES
    ('USD', 'US Dollar', 1.0, 1.0, 'base_currency', CURRENT_DATE),
    ('EUR', 'Euro', 1.09, 0.92, 'initial_seed', CURRENT_DATE),
    ('BRL', 'Brazilian Real', 0.20, 5.00, 'initial_seed', CURRENT_DATE),
    ('GBP', 'British Pound', 1.27, 0.79, 'initial_seed', CURRENT_DATE),
    ('CAD', 'Canadian Dollar', 0.71, 1.41, 'initial_seed', CURRENT_DATE),
    ('AUD', 'Australian Dollar', 0.63, 1.59, 'initial_seed', CURRENT_DATE),
    ('JPY', 'Japanese Yen', 0.0067, 149.5, 'initial_seed', CURRENT_DATE),
    ('CNY', 'Chinese Yuan', 0.14, 7.25, 'initial_seed', CURRENT_DATE),
    ('INR', 'Indian Rupee', 0.012, 83.5, 'initial_seed', CURRENT_DATE),
    ('MXN', 'Mexican Peso', 0.050, 20.0, 'initial_seed', CURRENT_DATE)
ON CONFLICT (currency_code, valid_from) DO NOTHING;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

/*
-- Get current USD exchange rate for BRL
SELECT sofia.get_exchange_rate('BRL');
-- Returns: 0.20

-- Convert 10000 BRL to USD
SELECT sofia.convert_currency(10000, 'BRL', 'USD');
-- Returns: 2000.00

-- Convert 150000 USD to BRL
SELECT sofia.convert_currency(150000, 'USD', 'BRL');
-- Returns: 750000.00

-- Convert EUR to BRL
SELECT sofia.convert_currency(5000, 'EUR', 'BRL');
-- Returns: ~27250.00

-- Get historical rate
SELECT sofia.get_exchange_rate('EUR', '2025-01-01');

-- View all current rates
SELECT
    currency_code,
    currency_name,
    rate_to_usd,
    '1 ' || currency_code || ' = ' || rate_to_usd || ' USD' as conversion,
    valid_from
FROM sofia.currency_rates
WHERE valid_from = CURRENT_DATE
ORDER BY currency_code;
*/
