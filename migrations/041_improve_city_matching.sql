-- Migration 041: Improve City Matching (Opção 3)
-- Date: 2025-12-26
-- Purpose: Better matching of existing 874 cities
--
-- Strategies:
-- 1. Case-insensitive matching
-- 2. Accent-insensitive (São Paulo = Sao Paulo)
-- 3. Common aliases (München = Munich, NYC = New York)

BEGIN;

-- ============================================================================
-- STEP 1: Case-insensitive + country match
-- ============================================================================

UPDATE sofia.jobs j
SET city_id = c.id
FROM sofia.cities c
WHERE j.city_id IS NULL
  AND j.city IS NOT NULL
  AND j.country_id IS NOT NULL
  AND LOWER(j.city) = LOWER(c.name)
  AND c.country_id = j.country_id;

-- ============================================================================
-- STEP 2: Unaccent matching (São Paulo = Sao Paulo, etc.)
-- ============================================================================

-- CREATE EXTENSION IF NOT EXISTS unaccent;

-- For now, manual common cases:
UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'São Paulo' AND country_id = 2 LIMIT 1)
WHERE city_id IS NULL
  AND LOWER(city) IN ('sao paulo', 'são paulo', 'saulo paulo');

UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'Brasília' AND country_id = 2 LIMIT 1)
WHERE city_id IS NULL
  AND LOWER(city) IN ('brasilia', 'brasília');

-- ============================================================================
-- STEP 3: Common city aliases
-- ============================================================================

-- NYC → New York
UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'New York' AND country_id = 1 LIMIT 1)
WHERE city_id IS NULL
  AND city IN ('NYC', 'New York City');

-- SF → San Francisco
UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'San Francisco' AND country_id = 1 LIMIT 1)
WHERE city_id IS NULL
  AND city IN ('SF', 'San Fran');

-- München → Munich
UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'Munich' AND country_id = 6 LIMIT 1)
WHERE city_id IS NULL
  AND city IN ('München', 'Munchen');

-- Wien → Vienna
UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'Vienna' AND country_id = 28 LIMIT 1)
WHERE city_id IS NULL
  AND city IN ('Wien');

-- Bangalore → Bengaluru
UPDATE sofia.jobs
SET city_id = (SELECT id FROM sofia.cities WHERE name = 'Bengaluru' AND country_id = 8 LIMIT 1)
WHERE city_id IS NULL
  AND city IN ('Bangalore');

-- ============================================================================
-- STATISTICS
-- ============================================================================

DO $$
DECLARE
  job_city_count INTEGER;
  job_city_pct NUMERIC;
BEGIN
  SELECT COUNT(city_id), ROUND(100.0 * COUNT(city_id) / COUNT(*), 1)
  INTO job_city_count, job_city_pct
  FROM sofia.jobs;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'MIGRATION 041 - Improve Matching';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Jobs with city_id: % (%)', job_city_count, job_city_pct;
  RAISE NOTICE '========================================';

  IF job_city_pct >= 80.0 THEN
    RAISE NOTICE '🎉 TARGET 80 PERCENT ACHIEVED!';
  ELSE
    RAISE NOTICE 'Gap to 80: % pp', 80.0 - job_city_pct;
  END IF;

  RAISE NOTICE '========================================';
END $$;

COMMIT;
