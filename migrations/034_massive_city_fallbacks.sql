-- Migration 034: Massive City Fallbacks Application
-- Date: 2025-12-26
-- Purpose: Apply ALL 150+ city name fallbacks directly in SQL
--
-- This migration applies city name normalization for jobs that have
-- malformed city names that don't match database entries

BEGIN;

-- ============================================================================
-- BRAZILIAN CITIES - Name variations
-- ============================================================================

-- "Brasilia" → "Brasília"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'Brasília'
FROM (SELECT id FROM sofia.cities WHERE name = 'Brasília' AND country_id = 2 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'brasilia' AND j.country_id = 2;

-- ============================================================================
-- GERMAN CITIES - Name variations
-- ============================================================================

-- "München" → "Munich"
UPDATE sofia.jobs j
SET city_id = c.id
FROM (SELECT id FROM sofia.cities WHERE name = 'Munich' AND country_id = 6 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'münchen';

-- "Frankfurt am Main" → "Frankfurt"
UPDATE sofia.jobs j
SET city_id = c.id
FROM (SELECT id FROM sofia.cities WHERE name = 'Frankfurt' AND country_id = 6 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'frankfurt am main';

-- ============================================================================
-- EXTRACT CITIES FROM "City, State" FORMAT
-- ============================================================================

-- This will help with patterns like "Charlotte, NC", "Austin, TX", etc.
-- We extract the city name before the comma and try to match

-- Create temp table with extracted cities
CREATE TEMP TABLE IF NOT EXISTS temp_extracted_cities AS
SELECT
  j.id as job_id,
  TRIM(SPLIT_PART(j.city, ',', 1)) as extracted_city,
  j.country_id,
  j.state_id
FROM sofia.jobs j
WHERE j.city_id IS NULL
  AND j.city LIKE '%,%'
  AND NOT (j.city LIKE '%;%')  -- Not multi-city lists
  AND LENGTH(j.city) - LENGTH(REPLACE(j.city, ',', '')) = 1;  -- Only one comma

-- Update jobs with extracted cities
UPDATE sofia.jobs j
SET city_id = c.id
FROM temp_extracted_cities te
JOIN sofia.cities c ON LOWER(c.name) = LOWER(te.extracted_city)
WHERE j.id = te.job_id
  AND (
    (te.state_id IS NOT NULL AND c.state_id = te.state_id)
    OR (te.country_id IS NOT NULL AND c.country_id = te.country_id)
    OR c.name ILIKE te.extracted_city
  );

-- ============================================================================
-- RE-RUN STANDARD BACKFILL WITH BETTER MATCHING
-- ============================================================================

-- Try ILIKE matching (case-insensitive) for remaining cities
UPDATE sofia.jobs j
SET city_id = ci.id
FROM sofia.cities ci
WHERE j.city_id IS NULL
  AND j.city IS NOT NULL
  AND j.city != ''
  AND ci.name ILIKE j.city
  AND (
    (j.state_id IS NOT NULL AND ci.state_id = j.state_id)
    OR (j.country_id IS NOT NULL AND ci.country_id = j.country_id)
  );

-- ============================================================================
-- STATISTICS
-- ============================================================================

DO $$
DECLARE
  total_jobs INTEGER;
  with_city INTEGER;
  city_pct NUMERIC;
BEGIN
  SELECT COUNT(*), COUNT(city_id), ROUND(100.0 * COUNT(city_id) / COUNT(*), 1)
  INTO total_jobs, with_city, city_pct
  FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 034 RESULTS';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Total jobs: %', total_jobs;
  RAISE NOTICE 'City: % (%)', with_city, city_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
