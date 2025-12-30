-- Complete Gender Data Migration (remaining parts)
-- Step 6: Central Banks (2,225 records)
-- Step 7: Eurostat (807,866 records)

-- Step 6: Migrate data from central_banks_women_data
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
-- This will take time due to size
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

-- Verify migration
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
