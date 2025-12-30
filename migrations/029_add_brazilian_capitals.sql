-- Migration 029: Add Brazilian State Capitals
-- Date: 2025-12-26
-- Purpose: Add 24 missing Brazilian state capitals to sofia.cities table
--
-- Context: Only 3/27 Brazilian capitals were in the database (São Paulo, Belo Horizonte, Porto Velho)
-- This causes 242+ jobs from Aracaju alone to not have city_id mapped
-- After this migration, we can run a backfill to update existing jobs

BEGIN;

-- Insert Brazilian capitals with their corresponding state_id and country_id (Brazil = 2)
INSERT INTO sofia.cities (name, state_id, country_id) VALUES
  -- Southeast
  ('Rio de Janeiro', 953, 2),  -- RJ

  -- South
  ('Curitiba', 950, 2),         -- PR
  ('Florianópolis', 958, 2),    -- SC
  ('Porto Alegre', 955, 2),     -- RS

  -- Northeast
  ('Aracaju', 960, 2),          -- SE - 242 jobs waiting for this!
  ('Fortaleza', 940, 2),        -- CE
  ('João Pessoa', 949, 2),      -- PB
  ('Maceió', 936, 2),           -- AL
  ('Natal', 954, 2),            -- RN
  ('Recife', 951, 2),           -- PE
  ('Salvador', 939, 2),         -- BA
  ('São Luís', 944, 2),         -- MA
  ('Teresina', 952, 2),         -- PI

  -- North
  ('Belém', 948, 2),            -- PA
  ('Boa Vista', 957, 2),        -- RR
  ('Macapá', 937, 2),           -- AP
  ('Manaus', 938, 2),           -- AM
  ('Palmas', 961, 2),           -- TO
  ('Rio Branco', 935, 2),       -- AC

  -- Central-West
  ('Brasília', 941, 2),         -- DF
  ('Campo Grande', 946, 2),     -- MS
  ('Cuiabá', 945, 2),           -- MT
  ('Goiânia', 943, 2),          -- GO

  -- East
  ('Vitória', 942, 2)           -- ES

ON CONFLICT (name, state_id, country_id) DO NOTHING;

-- Verify insertion
DO $$
DECLARE
  capital_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO capital_count
  FROM sofia.cities
  WHERE country_id = 2
  AND name IN (
    'Aracaju', 'Belém', 'Belo Horizonte', 'Boa Vista', 'Brasília',
    'Campo Grande', 'Cuiabá', 'Curitiba', 'Florianópolis', 'Fortaleza',
    'Goiânia', 'João Pessoa', 'Macapá', 'Maceió', 'Manaus',
    'Natal', 'Palmas', 'Porto Alegre', 'Porto Velho', 'Recife',
    'Rio Branco', 'Rio de Janeiro', 'Salvador', 'São Luís', 'São Paulo',
    'Teresina', 'Vitória'
  );

  RAISE NOTICE '✅ Brazilian capitals in database: % / 27', capital_count;

  IF capital_count < 27 THEN
    RAISE WARNING '⚠️  Some capitals are still missing';
  END IF;
END $$;

COMMIT;
