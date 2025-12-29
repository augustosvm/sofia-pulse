-- Migration 032: Add More Brazilian Cities
-- Date: 2025-12-26
-- Purpose: Add 17 major Brazilian cities found in job listings
--
-- Context: Analysis showed 100+ jobs from these cities without city_id
-- Cities include: Greater São Paulo metro area, state capitals, and regional hubs

BEGIN;

-- Insert Brazilian cities with their corresponding state_id and country_id (Brazil = 2)
INSERT INTO sofia.cities (name, state_id, country_id) VALUES
  -- São Paulo State (SP = 959) - 9 cities
  ('Barueri', 959, 2),
  ('Osasco', 959, 2),
  ('Cotia', 959, 2),
  ('Santo André', 959, 2),
  ('Ribeirão Preto', 959, 2),
  ('Guarulhos', 959, 2),
  ('Campinas', 959, 2),
  ('Indaiatuba', 959, 2),
  ('Jandira', 959, 2),

  -- Minas Gerais (MG = 947) - 2 cities
  ('Contagem', 947, 2),
  ('Ituiutaba', 947, 2),

  -- Paraná (PR = 950) - 1 city
  ('Cascavel', 950, 2),

  -- Santa Catarina (SC = 958) - 2 cities
  ('Joinville', 958, 2),
  ('Balneário Camboriú', 958, 2),

  -- Rio Grande do Sul (RS = 955) - 2 cities
  ('Canoas', 955, 2),
  ('São Leopoldo', 955, 2),

  -- Goiás (GO = 943) - 1 city
  ('Anápolis', 943, 2)

ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- Verify insertion
DO $$
DECLARE
  inserted_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO inserted_count
  FROM sofia.cities
  WHERE country_id = 2
  AND name IN (
    'Barueri', 'Osasco', 'Cotia', 'Santo André', 'Ribeirão Preto',
    'Guarulhos', 'Campinas', 'Indaiatuba', 'Jandira', 'Contagem',
    'Ituiutaba', 'Cascavel', 'Joinville', 'Balneário Camboriú',
    'Canoas', 'São Leopoldo', 'Anápolis'
  );

  RAISE NOTICE '✅ Brazilian cities now in database: % / 17', inserted_count;

  IF inserted_count < 17 THEN
    RAISE WARNING '⚠️  Some cities were not inserted (may already exist)';
  END IF;
END $$;

COMMIT;
