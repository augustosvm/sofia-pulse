-- Migration: Backfill Geographic IDs
-- Popula country_id, state_id, city_id a partir de country, state, city (strings)
-- Depois disso, as colunas antigas podem ser removidas

BEGIN;

-- ============================================================================
-- 1. BACKFILL JOBS TABLE
-- ============================================================================

-- Update country_id from country string
UPDATE sofia.jobs j
SET country_id = c.id
FROM sofia.countries c
WHERE j.country_id IS NULL
  AND j.country IS NOT NULL
  AND (
    c.common_name ILIKE j.country
    OR c.official_name ILIKE j.country
    OR c.iso_alpha2 = j.country
    OR c.iso_alpha3 = j.country
  );

-- Update state_id from state string
UPDATE sofia.jobs j
SET state_id = s.id
FROM sofia.states s
WHERE j.state_id IS NULL
  AND j.state IS NOT NULL
  AND j.country_id IS NOT NULL
  AND s.country_id = j.country_id
  AND (
    s.name ILIKE j.state
    OR s.code = j.state
  );

-- Update city_id from city string
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
-- 2. BACKFILL FUNDING_ROUNDS TABLE
-- ============================================================================

-- Update country_id from country string
UPDATE sofia.funding_rounds fr
SET country_id = c.id
FROM sofia.countries c
WHERE fr.country_id IS NULL
  AND fr.country IS NOT NULL
  AND (
    c.common_name ILIKE fr.country
    OR c.official_name ILIKE fr.country
    OR c.iso_alpha2 = fr.country
    OR c.iso_alpha3 = fr.country
  );

-- Update city_id from city string
UPDATE sofia.funding_rounds fr
SET city_id = ci.id
FROM sofia.cities ci
WHERE fr.city_id IS NULL
  AND fr.city IS NOT NULL
  AND fr.country_id IS NOT NULL
  AND ci.country_id = fr.country_id
  AND ci.name ILIKE fr.city;

-- ============================================================================
-- 3. STATISTICS
-- ============================================================================

DO $$
DECLARE
  jobs_country_coverage NUMERIC;
  jobs_city_coverage NUMERIC;
  funding_country_coverage NUMERIC;
  funding_city_coverage NUMERIC;
BEGIN
  -- Jobs coverage
  SELECT
    ROUND(COUNT(country_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1),
    ROUND(COUNT(city_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1)
  INTO jobs_country_coverage, jobs_city_coverage
  FROM sofia.jobs;

  -- Funding coverage
  SELECT
    ROUND(COUNT(country_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1),
    ROUND(COUNT(city_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1)
  INTO funding_country_coverage, funding_city_coverage
  FROM sofia.funding_rounds;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'BACKFILL RESULTS';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Jobs:';
  RAISE NOTICE '  country_id coverage: %', jobs_country_coverage;
  RAISE NOTICE '  city_id coverage: %', jobs_city_coverage;
  RAISE NOTICE 'Funding Rounds:';
  RAISE NOTICE '  country_id coverage: %', funding_country_coverage;
  RAISE NOTICE '  city_id coverage: %', funding_city_coverage;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
