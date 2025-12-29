-- Migration 037: Cleanup Invalid Cities
-- Date: 2025-12-26
-- Purpose: Remove invalid city entries added in migration 036
--
-- Some patterns like "In-Office", "Brasil" (country names) were incorrectly
-- added as cities

BEGIN;

-- ============================================================================
-- STEP 1: Delete invalid cities from database
-- ============================================================================

DELETE FROM sofia.cities
WHERE name IN (
  'In-Office', 'Distributed', 'N/A', 'NA', 'LOCATION', 'TBD',
  -- Country names that were added as cities
  'Brasil', 'Deutschland', 'Nederland', 'Mexico', 'Japan', 'Korea',
  'United Kingdom', 'Brazil', 'Österreich'
);

-- ============================================================================
-- STEP 2: Set city = NULL for jobs that have country names as city
-- ============================================================================

UPDATE sofia.jobs
SET city = NULL, city_id = NULL
WHERE city IN (
  'In-Office', 'Distributed', 'N/A', 'NA', 'LOCATION', 'TBD',
  'Brasil', 'Deutschland', 'Nederland', 'Mexico', 'Japan', 'Korea',
  'United Kingdom', 'Brazil', 'Österreich'
);

-- ============================================================================
-- STATISTICS
-- ============================================================================

DO $$
DECLARE
  city_count INTEGER;
  job_city_pct NUMERIC;
BEGIN
  SELECT COUNT(*) INTO city_count FROM sofia.cities;
  SELECT ROUND(100.0 * COUNT(city_id) / COUNT(*), 1) INTO job_city_pct FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 037 - Cleanup';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Cities in database: %', city_count;
  RAISE NOTICE 'Job city coverage: %', job_city_pct;
  RAISE NOTICE '========================================';
END $$;

COMMIT;
