-- Migration 028: Add USD Normalized Salary Columns to Jobs
-- Created: 2025-12-24
-- Purpose: Enable global salary comparisons by normalizing all salaries to USD

-- ============================================================================
-- ADD USD SALARY COLUMNS
-- ============================================================================

ALTER TABLE sofia.jobs
ADD COLUMN IF NOT EXISTS salary_min_usd NUMERIC(12, 2),
ADD COLUMN IF NOT EXISTS salary_max_usd NUMERIC(12, 2),
ADD COLUMN IF NOT EXISTS salary_avg_usd NUMERIC(12, 2) GENERATED ALWAYS AS (
    CASE
        WHEN salary_min_usd IS NOT NULL AND salary_max_usd IS NOT NULL
        THEN (salary_min_usd + salary_max_usd) / 2
        WHEN salary_min_usd IS NOT NULL THEN salary_min_usd
        WHEN salary_max_usd IS NOT NULL THEN salary_max_usd
        ELSE NULL
    END
) STORED,
ADD COLUMN IF NOT EXISTS salary_currency_rate NUMERIC(12, 6),
ADD COLUMN IF NOT EXISTS salary_converted_at TIMESTAMP;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_jobs_salary_min_usd ON sofia.jobs(salary_min_usd) WHERE salary_min_usd IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_salary_max_usd ON sofia.jobs(salary_max_usd) WHERE salary_max_usd IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_salary_avg_usd ON sofia.jobs(salary_avg_usd) WHERE salary_avg_usd IS NOT NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN sofia.jobs.salary_min_usd IS 'Minimum salary converted to USD using current exchange rates';
COMMENT ON COLUMN sofia.jobs.salary_max_usd IS 'Maximum salary converted to USD using current exchange rates';
COMMENT ON COLUMN sofia.jobs.salary_avg_usd IS 'Average salary in USD (auto-calculated from min/max)';
COMMENT ON COLUMN sofia.jobs.salary_currency_rate IS 'Exchange rate used for conversion (for audit trail)';
COMMENT ON COLUMN sofia.jobs.salary_converted_at IS 'Timestamp when salary was converted to USD';

-- ============================================================================
-- HELPER FUNCTION: Convert Job Salary to USD
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.convert_job_salary_to_usd(
    p_job_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_currency VARCHAR(10);
    v_min NUMERIC;
    v_max NUMERIC;
    v_rate NUMERIC;
BEGIN
    -- Get job salary info
    SELECT salary_currency, salary_min, salary_max
    INTO v_currency, v_min, v_max
    FROM sofia.jobs
    WHERE id = p_job_id;

    -- Skip if no salary values at all
    IF v_min IS NULL AND v_max IS NULL THEN
        RETURN;
    END IF;

    -- If currency is USD or NULL, just copy values
    IF v_currency IS NULL OR UPPER(v_currency) = 'USD' THEN
        UPDATE sofia.jobs
        SET salary_min_usd = v_min,
            salary_max_usd = v_max,
            salary_currency_rate = 1.0,
            salary_converted_at = NOW()
        WHERE id = p_job_id;
        RETURN;
    END IF;

    -- Get exchange rate
    v_rate := sofia.get_exchange_rate(v_currency);

    -- Skip if rate not found
    IF v_rate IS NULL THEN
        RETURN;
    END IF;

    -- Convert and update
    UPDATE sofia.jobs
    SET salary_min_usd = CASE WHEN v_min IS NOT NULL THEN ROUND(v_min * v_rate, 2) ELSE NULL END,
        salary_max_usd = CASE WHEN v_max IS NOT NULL THEN ROUND(v_max * v_rate, 2) ELSE NULL END,
        salary_currency_rate = v_rate,
        salary_converted_at = NOW()
    WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- BATCH CONVERSION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.convert_all_jobs_to_usd(
    p_limit INTEGER DEFAULT 1000
) RETURNS TABLE(
    total_processed INTEGER,
    total_converted INTEGER,
    total_skipped INTEGER
) AS $$
DECLARE
    v_processed INTEGER := 0;
    v_converted INTEGER := 0;
    v_skipped INTEGER := 0;
    v_job_id INTEGER;
BEGIN
    -- Convert jobs that haven't been converted yet or need update
    FOR v_job_id IN
        SELECT id
        FROM sofia.jobs
        WHERE (salary_min IS NOT NULL OR salary_max IS NOT NULL)
          AND salary_currency IS NOT NULL
          AND (salary_converted_at IS NULL OR salary_converted_at < NOW() - INTERVAL '7 days')
        ORDER BY id
        LIMIT p_limit
    LOOP
        BEGIN
            PERFORM sofia.convert_job_salary_to_usd(v_job_id);
            v_converted := v_converted + 1;
        EXCEPTION WHEN OTHERS THEN
            v_skipped := v_skipped + 1;
        END;
        v_processed := v_processed + 1;
    END LOOP;

    RETURN QUERY SELECT v_processed, v_converted, v_skipped;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

/*
-- Convert single job
SELECT sofia.convert_job_salary_to_usd(12345);

-- Batch convert up to 1000 jobs
SELECT * FROM sofia.convert_all_jobs_to_usd(1000);

-- View jobs with USD salaries
SELECT
    title,
    company,
    salary_min,
    salary_max,
    salary_currency,
    salary_min_usd,
    salary_max_usd,
    salary_avg_usd,
    '1 ' || salary_currency || ' = ' || salary_currency_rate || ' USD' as rate_used
FROM sofia.jobs
WHERE salary_min_usd IS NOT NULL
ORDER BY salary_avg_usd DESC
LIMIT 20;

-- Global salary comparison by country
SELECT
    country,
    COUNT(*) as job_count,
    ROUND(AVG(salary_avg_usd)) as avg_salary_usd,
    ROUND(MIN(salary_min_usd)) as min_salary_usd,
    ROUND(MAX(salary_max_usd)) as max_salary_usd
FROM sofia.jobs
WHERE salary_avg_usd IS NOT NULL
GROUP BY country
ORDER BY avg_salary_usd DESC;

-- Top paying tech skills globally
SELECT
    UNNEST(skills_required) as skill,
    COUNT(*) as job_count,
    ROUND(AVG(salary_avg_usd)) as avg_salary_usd
FROM sofia.jobs
WHERE salary_avg_usd IS NOT NULL
  AND skills_required IS NOT NULL
GROUP BY skill
HAVING COUNT(*) >= 10
ORDER BY avg_salary_usd DESC
LIMIT 20;
*/
