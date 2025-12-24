-- Migration: Consolidate Gender Data (5 tables → 1 unified table)
-- Purpose: Merge women_eurostat_data, women_world_bank_data, women_ilo_data, central_banks_women_data → gender_indicators
-- Total: ~878,000 records

-- Step 1: Expand gender_indicators table to accommodate all fields from 5 sources
ALTER TABLE sofia.gender_indicators
ADD COLUMN IF NOT EXISTS region VARCHAR(50),
ADD COLUMN IF NOT EXISTS sex VARCHAR(10),
ADD COLUMN IF NOT EXISTS age_group VARCHAR(50),
ADD COLUMN IF NOT EXISTS dataset_code VARCHAR(100),
ADD COLUMN IF NOT EXISTS dataset_name TEXT,
ADD COLUMN IF NOT EXISTS category VARCHAR(100),
ADD COLUMN IF NOT EXISTS unit VARCHAR(50),
ADD COLUMN IF NOT EXISTS central_bank_code VARCHAR(50),
ADD COLUMN IF NOT EXISTS central_bank_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Step 2: Create unique constraint to prevent duplicates
-- (indicator_code + country_code + year + sex + age_group + dataset_code)
CREATE UNIQUE INDEX IF NOT EXISTS idx_gender_indicators_unique
ON sofia.gender_indicators (
  indicator_code,
  country_code,
  year,
  COALESCE(sex, ''),
  COALESCE(age_group, ''),
  COALESCE(dataset_code, '')
);

-- Step 3: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_gender_indicators_source ON sofia.gender_indicators(source);
CREATE INDEX IF NOT EXISTS idx_gender_indicators_category ON sofia.gender_indicators(category);
CREATE INDEX IF NOT EXISTS idx_gender_indicators_region ON sofia.gender_indicators(region);
CREATE INDEX IF NOT EXISTS idx_gender_indicators_sex ON sofia.gender_indicators(sex);

-- Step 4: Migrate data from women_world_bank_data (62,700 records)
INSERT INTO sofia.gender_indicators (
  indicator_code,
  indicator_name,
  country_code,
  country_name,
  year,
  value,
  category,
  source,
  collected_at,
  created_at,
  updated_at
)
SELECT
  indicator_code,
  indicator_name,
  country_code,
  country_name,
  year,
  value,
  indicator_category as category,
  'World Bank' as source,
  collected_at,
  created_at,
  updated_at
FROM sofia.women_world_bank_data
ON CONFLICT (indicator_code, country_code, year, COALESCE(sex, ''), COALESCE(age_group, ''), COALESCE(dataset_code, ''))
DO UPDATE SET
  value = EXCLUDED.value,
  indicator_name = COALESCE(EXCLUDED.indicator_name, sofia.gender_indicators.indicator_name),
  country_name = COALESCE(EXCLUDED.country_name, sofia.gender_indicators.country_name),
  category = COALESCE(EXCLUDED.category, sofia.gender_indicators.category),
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 5: Migrate data from women_ilo_data (3,825 records)
INSERT INTO sofia.gender_indicators (
  indicator_code,
  indicator_name,
  country_code,
  country_name,
  year,
  value,
  sex,
  age_group,
  category,
  source,
  collected_at,
  created_at,
  updated_at
)
SELECT
  indicator_id as indicator_code,
  indicator_name,
  country_code,
  country_name,
  year,
  value,
  sex,
  age_group,
  category,
  'ILO' as source,
  collected_at,
  created_at,
  updated_at
FROM sofia.women_ilo_data
ON CONFLICT (indicator_code, country_code, year, COALESCE(sex, ''), COALESCE(age_group, ''), COALESCE(dataset_code, ''))
DO UPDATE SET
  value = EXCLUDED.value,
  sex = EXCLUDED.sex,
  age_group = EXCLUDED.age_group,
  indicator_name = COALESCE(EXCLUDED.indicator_name, sofia.gender_indicators.indicator_name),
  country_name = COALESCE(EXCLUDED.country_name, sofia.gender_indicators.country_name),
  category = COALESCE(EXCLUDED.category, sofia.gender_indicators.category),
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 6: Migrate data from central_banks_women_data (2,225 records)
INSERT INTO sofia.gender_indicators (
  indicator_code,
  indicator_name,
  country_code,
  year,
  value,
  region,
  central_bank_code,
  central_bank_name,
  source,
  collected_at,
  created_at,
  updated_at
)
SELECT
  indicator_code,
  indicator_name,
  country_code,
  year,
  value,
  region,
  central_bank_code,
  central_bank_name,
  'Central Banks' as source,
  collected_at,
  created_at,
  updated_at
FROM sofia.central_banks_women_data
ON CONFLICT (indicator_code, country_code, year, COALESCE(sex, ''), COALESCE(age_group, ''), COALESCE(dataset_code, ''))
DO UPDATE SET
  value = EXCLUDED.value,
  region = EXCLUDED.region,
  central_bank_code = EXCLUDED.central_bank_code,
  central_bank_name = EXCLUDED.central_bank_name,
  indicator_name = COALESCE(EXCLUDED.indicator_name, sofia.gender_indicators.indicator_name),
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 7: Migrate data from women_eurostat_data (807,866 records) - LARGEST
-- This will take time due to size, run in batches
INSERT INTO sofia.gender_indicators (
  indicator_code,
  indicator_name,
  country_code,
  year,
  value,
  sex,
  age_group,
  dataset_code,
  dataset_name,
  category,
  unit,
  source,
  collected_at,
  created_at,
  updated_at
)
SELECT
  dataset_code as indicator_code,
  dataset_name as indicator_name,
  country_code,
  year::int as year,
  value::numeric as value,
  sex,
  age_group,
  dataset_code,
  dataset_name,
  category,
  unit,
  'Eurostat' as source,
  collected_at,
  created_at,
  updated_at
FROM sofia.women_eurostat_data
WHERE year ~ '^[0-9]+$'  -- Only numeric years
ON CONFLICT (indicator_code, country_code, year, COALESCE(sex, ''), COALESCE(age_group, ''), COALESCE(dataset_code, ''))
DO UPDATE SET
  value = EXCLUDED.value,
  sex = EXCLUDED.sex,
  age_group = EXCLUDED.age_group,
  dataset_name = EXCLUDED.dataset_name,
  category = COALESCE(EXCLUDED.category, sofia.gender_indicators.category),
  unit = EXCLUDED.unit,
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 8: Add comments
COMMENT ON TABLE sofia.gender_indicators IS 'Unified table for all gender-related indicators from 5 sources: Eurostat, World Bank, ILO, Central Banks, and custom collections';
COMMENT ON COLUMN sofia.gender_indicators.source IS 'Data source: Eurostat, World Bank, ILO, Central Banks, custom';
COMMENT ON COLUMN sofia.gender_indicators.region IS 'Geographic region (for central banks data): americas, europe, asia';
COMMENT ON COLUMN sofia.gender_indicators.sex IS 'Gender: M, F, or null for aggregated data';
COMMENT ON COLUMN sofia.gender_indicators.age_group IS 'Age range: Y15-24, Y25-54, Y55-64, TOTAL, etc.';
COMMENT ON COLUMN sofia.gender_indicators.dataset_code IS 'Original dataset code from Eurostat or other sources';

-- Step 9: Verify migration
DO $$
DECLARE
  total_count INTEGER;
  source_breakdown TEXT;
BEGIN
  SELECT COUNT(*) INTO total_count FROM sofia.gender_indicators;

  SELECT string_agg(source || ': ' || count::text, ', ')
  INTO source_breakdown
  FROM (
    SELECT source, COUNT(*) as count
    FROM sofia.gender_indicators
    GROUP BY source
    ORDER BY count DESC
  ) s;

  RAISE NOTICE 'Migration complete!';
  RAISE NOTICE 'Total records in gender_indicators: %', total_count;
  RAISE NOTICE 'Source breakdown: %', source_breakdown;
END $$;

-- Step 10: After verification, old tables can be dropped with:
-- DROP TABLE sofia.women_world_bank_data;
-- DROP TABLE sofia.women_ilo_data;
-- DROP TABLE sofia.central_banks_women_data;
-- DROP TABLE sofia.women_eurostat_data;
-- (Keep commented until manual verification is complete)
