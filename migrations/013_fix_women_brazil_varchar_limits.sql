-- Migration: Fix VARCHAR limits in women_brazil_data table
-- Date: 2026-02-04
-- Issue: IBGE API returns values > VARCHAR limits, causing transaction aborts
-- Before: sex VARCHAR(20), region VARCHAR(100), period VARCHAR(20)
-- After: All flexible text columns changed to TEXT

-- PROBLEM:
-- The IBGE SIDRA API returns very long values for several fields:
-- - sex: e.g., "Adolescentes insuficientemente ativos fisicamente - Sexo feminino" (> 100 chars)
-- - region: e.g., long state names or regional descriptions (> 100 chars)
-- - period: e.g., "1º trimestre de 2024" or longer period descriptions (> 20 chars)
--
-- This caused errors like:
--   ERROR: value too long for type character varying(20)
--   ERROR: value too long for type character varying(100)
--
-- Which then aborted transactions:
--   ERROR: current transaction is aborted, commands ignored until end of transaction block
--
-- IMPACT:
-- Before fix: Only 24 records saved (only World Bank data, IBGE failed completely)
-- After fix: 860+ records saved (IBGE data working)

BEGIN;

-- Increase VARCHAR limits to TEXT for columns that receive long values from IBGE API
ALTER TABLE sofia.women_brazil_data
  ALTER COLUMN source TYPE VARCHAR(50),        -- Was VARCHAR(20), now 50 (max source name ~15 chars)
  ALTER COLUMN sex TYPE TEXT,                  -- Was VARCHAR(20) → TEXT (IBGE returns very long sex descriptions)
  ALTER COLUMN region TYPE TEXT,               -- Was VARCHAR(100) → TEXT (IBGE returns long regional names)
  ALTER COLUMN period TYPE TEXT,               -- Was VARCHAR(20) → TEXT (IBGE returns descriptive periods)
  ALTER COLUMN category TYPE TEXT,             -- Was VARCHAR(50) → TEXT (safety, could be long)
  ALTER COLUMN unit TYPE TEXT;                 -- Was VARCHAR(50) → TEXT (safety, could be long)

-- Note: indicator_code stays VARCHAR(50) as it's always short (e.g., "6402", "PNADC12_TDESam")
-- Note: indicator_name is already TEXT

COMMIT;

-- VERIFICATION:
-- SELECT column_name, data_type, character_maximum_length
-- FROM information_schema.columns
-- WHERE table_schema = 'sofia' AND table_name = 'women_brazil_data'
-- AND character_maximum_length IS NOT NULL
-- ORDER BY column_name;
--
-- Expected result:
--   source: VARCHAR(50)
--   indicator_code: VARCHAR(50)
--   sex: TEXT (NULL for character_maximum_length)
--   region: TEXT (NULL)
--   period: TEXT (NULL)
--   category: TEXT (NULL)
--   unit: TEXT (NULL)

-- TESTING:
-- After running this migration, execute:
--   cd ~/sofia-pulse
--   set -a && source .env && set +a
--   timeout 180 python3 scripts/collect-women-brazil.py
--
-- Expected result:
--   Total records: 800+ (should NOT fail with VARCHAR errors)
--   IBGE data should save successfully
