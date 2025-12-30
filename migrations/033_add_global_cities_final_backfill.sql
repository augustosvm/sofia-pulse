-- Migration 033: Add Global Cities + Final Comprehensive Backfill
-- Date: 2025-12-26
-- Purpose: Add 24 missing global cities and apply all new fallbacks
--
-- Target: Reach 60%+ city_id coverage

BEGIN;

-- ============================================================================
-- STEP 1: Add Missing Global Cities
-- ============================================================================

INSERT INTO sofia.cities (name, state_id, country_id) VALUES
  -- Germany (6) - 9 cities
  ('Nuremberg', NULL, 6),
  ('Regensburg', NULL, 6),
  ('Würzburg', NULL, 6),
  ('Mannheim', NULL, 6),
  ('Leipzig', NULL, 6),
  ('Braunschweig', NULL, 6),
  ('Dortmund', NULL, 6),
  ('Bonn', NULL, 6),
  ('Jena', NULL, 6),

  -- United Kingdom (3) - 5 cities
  ('Nottingham', NULL, 3),
  ('Bath', NULL, 3),
  ('Brighton', NULL, 3),
  ('Newcastle Upon Tyne', NULL, 3),
  ('York', NULL, 3),

  -- Poland (22) - 3 cities
  ('Kraków', NULL, 22),
  ('Gliwice', NULL, 22),
  ('Wrocław', NULL, 22),

  -- Others
  ('Belgrade', NULL, 1034),  -- Serbia
  ('Calgary', NULL, 4),      -- Canada
  ('Stockholm', NULL, 23),   -- Sweden
  ('Toulouse', NULL, 7),     -- France
  ('Port Elizabeth', NULL, 32),  -- South Africa
  ('Canberra', NULL, 5),     -- Australia
  ('Wellington', NULL, 31)   -- New Zealand

ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- ============================================================================
-- STEP 2: Apply Brazilian Partial Name Fallbacks
-- ============================================================================

-- "Andre" → "Santo André"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'Santo André'
FROM (SELECT id FROM sofia.cities WHERE name = 'Santo André' AND country_id = 2 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'andre';

-- "Preto" → "Ribeirão Preto"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'Ribeirão Preto'
FROM (SELECT id FROM sofia.cities WHERE name = 'Ribeirão Preto' AND country_id = 2 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'preto';

-- "Campo" → "Campo Grande"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'Campo Grande'
FROM (SELECT id FROM sofia.cities WHERE name = 'Campo Grande' LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'campo';

-- "Sul" → "Porto Alegre"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'Porto Alegre'
FROM (SELECT id FROM sofia.cities WHERE name = 'Porto Alegre' AND country_id = 2 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'sul';

-- "Leopoldo" → "São Leopoldo"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'São Leopoldo'
FROM (SELECT id FROM sofia.cities WHERE name = 'São Leopoldo' AND country_id = 2 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'leopoldo';

-- "Camboriu" → "Balneário Camboriú"
UPDATE sofia.jobs j
SET city_id = c.id, city = 'Balneário Camboriú'
FROM (SELECT id FROM sofia.cities WHERE name = 'Balneário Camboriú' AND country_id = 2 LIMIT 1) c
WHERE j.city_id IS NULL AND LOWER(j.city) = 'camboriu';

-- ============================================================================
-- STEP 3: Re-run Standard Backfill (catches newly added cities)
-- ============================================================================

UPDATE sofia.jobs j
SET city_id = ci.id
FROM sofia.cities ci
WHERE j.city_id IS NULL
  AND j.city IS NOT NULL
  AND j.city != ''
  AND (
    (j.state_id IS NOT NULL AND ci.state_id = j.state_id AND ci.name ILIKE j.city)
    OR (j.country_id IS NOT NULL AND ci.country_id = j.country_id AND ci.name ILIKE j.city)
    OR (ci.name ILIKE j.city)
  );

-- ============================================================================
-- STEP 4: Final Statistics
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

  -- Improvement tracking
  initial_city_coverage CONSTANT NUMERIC := 37.1;
  initial_city_count CONSTANT INTEGER := 3825;

  city_gain INTEGER;
  pct_gain NUMERIC;
BEGIN
  -- Coverage stats
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

  city_gain := with_city - initial_city_count;
  pct_gain := city_pct - initial_city_coverage;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'FINAL COMPREHENSIVE RESULTS (Migration 033)';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Total jobs: %', total_jobs;
  RAISE NOTICE 'Country: % (%)', with_country, country_pct;
  RAISE NOTICE 'State: % (%)', with_state, state_pct;
  RAISE NOTICE 'City: % (%)', with_city, city_pct;
  RAISE NOTICE '';
  RAISE NOTICE 'Improvement:';
  RAISE NOTICE '  Start: % (%)', initial_city_count, initial_city_coverage;
  RAISE NOTICE '  Now: % (%)', with_city, city_pct;
  RAISE NOTICE '  Gain: +% jobs (+%pp)', city_gain, pct_gain;
  RAISE NOTICE '========================================';

  IF city_pct >= 60.0 THEN
    RAISE NOTICE '🎉 TARGET ACHIEVED: 60 percent city coverage reached!';
  ELSE
    RAISE NOTICE '⚠️  Target: 60 | Current: % | Gap: %', city_pct, 60.0 - city_pct;
  END IF;

  RAISE NOTICE '========================================';
END $$;

COMMIT;
