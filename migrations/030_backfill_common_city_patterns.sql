-- Migration 030: Backfill Common City Patterns
-- Date: 2025-12-26
-- Purpose: Update jobs with common malformed city names using intelligent patterns
--
-- This migration handles:
-- 1. Jobs where country/state are missing (preventing city match)
-- 2. Common city name variations ("Paulo" → "São Paulo", "Bay Area" → "San Francisco", etc.)
-- 3. Brazilian cities with state codes but no IDs

BEGIN;

-- ============================================================================
-- STEP 1: Fill missing country_id and state_id for Brazilian jobs
-- ============================================================================

-- Update country_id for jobs with state codes but no country
UPDATE sofia.jobs j
SET country_id = 2  -- Brazil
WHERE country_id IS NULL
  AND state IN ('AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO');

-- Update state_id for Brazilian jobs with 2-letter state codes
UPDATE sofia.jobs j
SET state_id = s.id
FROM sofia.states s
WHERE j.state_id IS NULL
  AND j.country_id = 2
  AND s.country_id = 2
  AND s.code = j.state;

-- ============================================================================
-- STEP 2: Update malformed city names directly
-- ============================================================================

-- "Paulo" → "São Paulo" (pick first match)
UPDATE sofia.jobs j
SET city_id = c.id
FROM (
  SELECT id FROM sofia.cities
  WHERE name = 'São Paulo' AND country_id = 2
  LIMIT 1
) c
WHERE j.city_id IS NULL
  AND j.city = 'Paulo';

-- "Sao Paulo" (without accent) → "São Paulo"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'São Paulo'
FROM (
  SELECT id FROM sofia.cities
  WHERE name = 'São Paulo' AND country_id = 2
  LIMIT 1
) c
WHERE j.city_id IS NULL
  AND LOWER(j.city) = 'sao paulo';

-- "San Francisco Bay Area" → "San Francisco"
UPDATE sofia.jobs j
SET city_id = c.id
FROM (
  SELECT id FROM sofia.cities
  WHERE name = 'San Francisco' AND country_id = 1
  LIMIT 1
) c
WHERE j.city_id IS NULL
  AND (j.city ILIKE '%san francisco bay area%' OR j.city ILIKE '%bay area%');

-- "NYC" → "New York"
UPDATE sofia.jobs j
SET city_id = c.id
FROM (
  SELECT id FROM sofia.cities
  WHERE name = 'New York' AND country_id = 1
  LIMIT 1
) c
WHERE j.city_id IS NULL
  AND (j.city = 'NYC' OR j.city = 'New York City');

-- "Bangalore" → "Bengaluru"
UPDATE sofia.jobs j
SET city_id = c.id
FROM (
  SELECT id FROM sofia.cities
  WHERE name = 'Bengaluru' AND country_id = 7
  LIMIT 1
) c
WHERE j.city_id IS NULL
  AND LOWER(j.city) = 'bangalore';

-- ============================================================================
-- STEP 3: Re-run standard backfill for newly populated country/state IDs
-- ============================================================================

-- Update city_id from city string (now that more jobs have country_id and state_id)
UPDATE sofia.jobs j
SET city_id = ci.id
FROM sofia.cities ci
WHERE j.city_id IS NULL
  AND j.city IS NOT NULL
  AND (
    (j.state_id IS NOT NULL AND ci.state_id = j.state_id AND ci.name ILIKE j.city)
    OR (j.country_id IS NOT NULL AND ci.country_id = j.country_id AND ci.name ILIKE j.city)
  );

-- ============================================================================
-- STEP 4: Statistics
-- ============================================================================

DO $$
DECLARE
  total_jobs INTEGER;
  with_country INTEGER;
  with_state INTEGER;
  with_city INTEGER;
  country_pct NUMERIC;
  state_pct NUMERIC;
  city_pct NUMERIC;
BEGIN
  SELECT
    COUNT(*),
    COUNT(country_id),
    COUNT(state_id),
    COUNT(city_id),
    ROUND(100.0 * COUNT(country_id) / COUNT(*), 1),
    ROUND(100.0 * COUNT(state_id) / COUNT(*), 1),
    ROUND(100.0 * COUNT(city_id) / COUNT(*), 1)
  INTO total_jobs, with_country, with_state, with_city, country_pct, state_pct, city_pct
  FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'BACKFILL RESULTS (Migration 030)';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Total jobs: %', total_jobs;
  RAISE NOTICE 'Country: % (%)', with_country, country_pct;
  RAISE NOTICE 'State: % (%)', with_state, state_pct;
  RAISE NOTICE 'City: % (%)', with_city, city_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
