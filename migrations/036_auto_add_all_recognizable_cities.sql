-- Migration 036: Auto-Add ALL Recognizable Cities
-- Date: 2025-12-26
-- Purpose: Automatically add every recognizable city (has valid name + country_id)
--
-- Philosophy: If a city is recognizable, it should be in the database!

BEGIN;

-- ============================================================================
-- STEP 1: Insert ALL recognizable cities into database
-- ============================================================================

-- Create cities from jobs that have:
-- - city name (not null/empty)
-- - country_id (known country)
-- - NOT Remote/Hybrid/placeholder patterns

INSERT INTO sofia.cities (name, state_id, country_id)
SELECT DISTINCT
  j.city as name,
  j.state_id,
  j.country_id
FROM sofia.jobs j
WHERE j.city_id IS NULL
  AND j.country_id IS NOT NULL
  AND j.city IS NOT NULL
  AND j.city != ''
  -- Filter out Remote/Hybrid patterns
  AND NOT (j.city ILIKE '%remote%' OR j.city ILIKE '%hybrid%' OR j.city ILIKE '%distributed%' OR j.city ILIKE '%flexible%')
  -- Filter out placeholders
  AND j.city NOT IN ('In-Office', 'LOCATION', 'N/A', 'NA', 'TBD', 'LATAM', 'EMEA', 'APAC')
  -- Filter out country names
  AND j.city NOT IN ('United States', 'USA', 'Canada', 'Brasil', 'Brazil', 'Mexico',
                     'India', 'China', 'Singapore', 'Portugal', 'Spain', 'España',
                     'France', 'Germany', 'Deutschland', 'UK', 'United Kingdom',
                     'Ireland', 'Australia', 'New Zealand', 'Philippines', 'Italy',
                     'Italia', 'Nederland', 'Netherlands', 'Schweiz', 'Switzerland',
                     'Österreich', 'Poland', 'Serbia', 'South Africa', 'Japan', 'Korea')
ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- ============================================================================
-- STEP 2: Update jobs with newly added cities
-- ============================================================================

UPDATE sofia.jobs j
SET city_id = c.id
FROM sofia.cities c
WHERE j.city_id IS NULL
  AND j.city IS NOT NULL
  AND j.country_id IS NOT NULL
  AND c.name = j.city
  AND c.country_id = j.country_id
  AND (
    (j.state_id IS NOT NULL AND c.state_id = j.state_id)
    OR (j.state_id IS NULL AND c.state_id IS NULL)
    OR c.state_id = j.state_id
  );

-- ============================================================================
-- STEP 3: Try fuzzy matching for remaining
-- ============================================================================

-- Case-insensitive match
UPDATE sofia.jobs j
SET city_id = c.id
FROM sofia.cities c
WHERE j.city_id IS NULL
  AND j.city IS NOT NULL
  AND j.country_id IS NOT NULL
  AND LOWER(c.name) = LOWER(j.city)
  AND c.country_id = j.country_id;

-- ============================================================================
-- STATISTICS
-- ============================================================================

DO $$
DECLARE
  total_jobs INTEGER;
  with_city INTEGER;
  city_pct NUMERIC;
  cities_added INTEGER;
BEGIN
  SELECT COUNT(*), COUNT(city_id), ROUND(100.0 * COUNT(city_id) / COUNT(*), 1)
  INTO total_jobs, with_city, city_pct
  FROM sofia.jobs;

  SELECT COUNT(*) INTO cities_added
  FROM sofia.cities
  WHERE country_id IS NOT NULL;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 036 - Auto-Add Cities';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Total cities in database: %', cities_added;
  RAISE NOTICE 'Jobs with city_id: % (%)', with_city, city_pct;
  RAISE NOTICE '========================================';

  IF city_pct >= 80.0 THEN
    RAISE NOTICE '🎉 TARGET ACHIEVED: 80 percent coverage!';
  ELSE
    RAISE NOTICE '⚠️  Target: 80 | Current: % | Gap: %', city_pct, 80.0 - city_pct;
  END IF;

  RAISE NOTICE '========================================';
END $$;

COMMIT;
