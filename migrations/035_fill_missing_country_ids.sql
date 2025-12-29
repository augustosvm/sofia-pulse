-- Migration 035: Fill Missing Country IDs
-- Date: 2025-12-26
-- Purpose: Infer country_id from location, state, or city patterns
--
-- Many jobs have cities but no country_id, preventing city matching

BEGIN;

-- ============================================================================
-- STEP 1: Infer from state codes (Brazilian states)
-- ============================================================================

UPDATE sofia.jobs j
SET country_id = 2  -- Brazil
WHERE country_id IS NULL
  AND state IN ('AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO');

-- ============================================================================
-- STEP 2: Infer from city/location patterns (country names in other languages)
-- ============================================================================

-- Jobs with city = "Deutschland" → Germany
UPDATE sofia.jobs
SET country_id = 6, city = NULL  -- Germany, clear city since it's the country
WHERE country_id IS NULL
  AND (city = 'Deutschland' OR location LIKE '%Deutschland%');

-- Jobs with city = "Brasil" → Brazil
UPDATE sofia.jobs
SET country_id = 2, city = NULL
WHERE country_id IS NULL
  AND city = 'Brasil';

-- Jobs with city = "Nederland" → Netherlands
UPDATE sofia.jobs
SET country_id = 24, city = NULL  -- Netherlands
WHERE country_id IS NULL
  AND city = 'Nederland';

-- Jobs with city = "Österreich" → Austria
UPDATE sofia.jobs
SET country_id = 33, city = NULL  -- Austria
WHERE country_id IS NULL
  AND (city = 'Österreich' OR city = 'Austria');

-- ============================================================================
-- STEP 3: Infer from location patterns (city, state/region format)
-- ============================================================================

-- "Burgwedel, Region Hannover" → Germany (has German region names)
UPDATE sofia.jobs j
SET country_id = c.id
FROM sofia.countries c
WHERE j.country_id IS NULL
  AND j.location IS NOT NULL
  AND c.common_name = 'Germany'
  AND (
    j.location LIKE '%Kreis%' OR
    j.location LIKE '%Bayern%' OR
    j.location LIKE '%Baden-Württemberg%' OR
    j.location LIKE '%Hessen%' OR
    j.location LIKE '%Nordrhein-Westfalen%'
  );

-- "Maassluis, Zuid-Holland" → Netherlands
UPDATE sofia.jobs j
SET country_id = c.id
FROM sofia.countries c
WHERE j.country_id IS NULL
  AND j.location IS NOT NULL
  AND c.common_name = 'Netherlands'
  AND (
    j.location LIKE '%Zuid-Holland%' OR
    j.location LIKE '%Noord-Holland%' OR
    j.location LIKE '%Noord-Brabant%' OR
    j.location LIKE '%Gelderland%' OR
    j.location LIKE '%Provincie Utrecht%'
  );

-- "Wels, Oberösterreich" → Austria
UPDATE sofia.jobs j
SET country_id = c.id
FROM sofia.countries c
WHERE j.country_id IS NULL
  AND j.location IS NOT NULL
  AND c.common_name = 'Austria'
  AND (
    j.location LIKE '%Oberösterreich%' OR
    j.location LIKE '%Steiermark%' OR
    j.location LIKE '%Graz-Umgebung%'
  );

-- "Brisbane, Brisbane Region" → Australia
UPDATE sofia.jobs j
SET country_id = c.id
FROM sofia.countries c
WHERE j.country_id IS NULL
  AND j.location IS NOT NULL
  AND c.common_name = 'Australia'
  AND (
    j.location LIKE '%Brisbane Region%' OR
    j.location LIKE '%Auckland City%' OR
    j.location LIKE '%Greater Wellington%' OR
    j.location LIKE '%Cape Town Region%'
  );

-- ============================================================================
-- STEP 4: Update state_id based on newly added country_id
-- ============================================================================

UPDATE sofia.jobs j
SET state_id = s.id
FROM sofia.states s
WHERE j.state_id IS NULL
  AND j.country_id IS NOT NULL
  AND s.country_id = j.country_id
  AND (
    s.code = j.state
    OR s.name ILIKE j.state
  );

-- ============================================================================
-- STATISTICS
-- ============================================================================

DO $$
DECLARE
  with_country INTEGER;
  country_pct NUMERIC;
BEGIN
  SELECT COUNT(country_id), ROUND(100.0 * COUNT(country_id) / COUNT(*), 1)
  INTO with_country, country_pct
  FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 035 - Country ID Backfill';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Jobs with country_id: % (%)', with_country, country_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
