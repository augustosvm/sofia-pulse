-- Migration 038: Aggressive Cleanup of Invalid Cities
-- Date: 2025-12-26
-- Purpose: Remove ALL invalid cities added in migration 036
--
-- Problem: Migration 036 added cities with wrong country_ids and invalid patterns

BEGIN;

-- ============================================================================
-- STEP 1: Clear city_id from jobs that reference invalid cities
-- ============================================================================

UPDATE sofia.jobs j
SET city_id = NULL
WHERE city_id IN (
  SELECT id FROM sofia.cities
  WHERE name IN (
    'United States', 'Canada', 'India', 'France', 'Australia', 'UK',
    'Germany', 'Spain', 'Italy', 'Portugal', 'Mexico', 'Brazil',
    'United Kingdom', 'Ireland', 'Singapore', 'Poland', 'Austria',
    'Netherlands', 'Switzerland', 'Sweden', 'Norway', 'Denmark',
    'Finland', 'Belgium', 'Japan', 'China', 'Korea', 'New Zealand',
    'NYC', 'SF', 'CHI', 'LA', 'DC', 'US'
  )
  OR name ILIKE '%remote%'
  OR name ILIKE '%hybrid%'
  OR LENGTH(name) <= 2
  OR name LIKE '%, %'
  OR name LIKE '%;%'
  OR (name = 'Chicago' AND country_id != 1)
  OR (name = 'Bellevue' AND country_id NOT IN (1, 4))
);

-- ============================================================================
-- STEP 2: Now delete invalid cities
-- ============================================================================

DELETE FROM sofia.cities
WHERE name IN (
  'United States', 'Canada', 'India', 'France', 'Australia', 'UK',
  'Germany', 'Spain', 'Italy', 'Portugal', 'Mexico', 'Brazil',
  'United Kingdom', 'Ireland', 'Singapore', 'Poland', 'Austria',
  'Netherlands', 'Switzerland', 'Sweden', 'Norway', 'Denmark',
  'Finland', 'Belgium', 'Japan', 'China', 'Korea', 'New Zealand',
  'NYC', 'SF', 'CHI', 'LA', 'DC', 'US'
)
OR name ILIKE '%remote%'
OR name ILIKE '%hybrid%'
OR LENGTH(name) <= 2
OR name LIKE '%, %'
OR name LIKE '%;%'
OR (name = 'Chicago' AND country_id != 1)
OR (name = 'Bellevue' AND country_id NOT IN (1, 4));

-- ============================================================================
-- STEP 4: Statistics
-- ============================================================================

DO $$
DECLARE
  city_count INTEGER;
  job_city_count INTEGER;
  job_city_pct NUMERIC;
BEGIN
  SELECT COUNT(*) INTO city_count FROM sofia.cities;
  SELECT COUNT(city_id), ROUND(100.0 * COUNT(city_id) / COUNT(*), 1)
  INTO job_city_count, job_city_pct
  FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 038 - Aggressive Cleanup';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Cities remaining: %', city_count;
  RAISE NOTICE 'Jobs with city_id: % (%)', job_city_count, job_city_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
