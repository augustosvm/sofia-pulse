-- Migration: Consolidate Jobs Tables (tech_jobs → jobs) - FIXED VERSION
-- Purpose: Merge tech_jobs into jobs (preserving 3,570 unique records)

-- Step 1: Ensure source column exists and has default
ALTER TABLE sofia.jobs
ADD COLUMN IF NOT EXISTS has_relocation BOOLEAN DEFAULT false;

ALTER TABLE sofia.jobs
ALTER COLUMN source SET DEFAULT 'unknown';

UPDATE sofia.jobs
SET source = 'unknown'
WHERE source IS NULL OR source = '';

-- Step 2: Remove duplicates from jobs table BEFORE creating unique index
-- Keep the most recent version of each duplicate
WITH duplicates AS (
  SELECT id,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(TRIM(title)), LOWER(TRIM(company)), DATE(posted_date)
      ORDER BY collected_at DESC NULLS LAST, id DESC
    ) as rn
  FROM sofia.jobs
)
DELETE FROM sofia.jobs
WHERE id IN (
  SELECT id FROM duplicates WHERE rn > 1
);

-- Step 3: Now create unique index (will succeed after deduplication)
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_unique_posting
ON sofia.jobs (
  LOWER(TRIM(title)),
  LOWER(TRIM(company)),
  DATE(posted_date)
);

-- Step 4: Migrate data from tech_jobs to jobs
INSERT INTO sofia.jobs (
  job_id,
  title,
  company,
  company_size,
  company_url,
  location,
  city,
  country,
  country_id,
  city_id,
  description,
  employment_type,
  seniority_level,
  remote_type,
  experience_years_min,
  experience_years_max,
  salary_min,
  salary_max,
  salary_currency,
  salary_period,
  has_health_insurance,
  has_equity,
  visa_sponsorship,
  has_relocation,
  skills_required,
  search_keyword,
  url,
  source, -- Map platform → source
  posted_date,
  collected_at,
  created_at,
  updated_at
)
SELECT
  job_id,
  title,
  company,
  company_size,
  company_url,
  location,
  city,
  country,
  country_id,
  city_id,
  description,
  employment_type,
  seniority_level,
  remote_type,
  experience_years_min,
  experience_years_max,
  salary_min,
  salary_max,
  salary_currency,
  salary_period,
  has_health_insurance,
  has_equity,
  has_visa_sponsorship as visa_sponsorship,
  has_relocation,
  skills_required,
  search_keyword,
  url,
  platform as source, -- CRITICAL: Map platform → source
  posted_date,
  collected_at,
  NOW() as created_at,
  NOW() as updated_at
FROM sofia.tech_jobs
ON CONFLICT (LOWER(TRIM(title)), LOWER(TRIM(company)), DATE(posted_date))
DO UPDATE SET
  description = CASE
    WHEN LENGTH(EXCLUDED.description) > LENGTH(sofia.jobs.description)
    THEN EXCLUDED.description
    ELSE sofia.jobs.description
  END,
  salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
  salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max),
  skills_required = COALESCE(EXCLUDED.skills_required, sofia.jobs.skills_required),
  company_size = COALESCE(EXCLUDED.company_size, sofia.jobs.company_size),
  company_url = COALESCE(EXCLUDED.company_url, sofia.jobs.company_url),
  country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
  city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
  updated_at = NOW();

-- Step 5: Add index on source
CREATE INDEX IF NOT EXISTS idx_jobs_source ON sofia.jobs(source);

-- Step 6: Verify migration
DO $$
DECLARE
  jobs_final INTEGER;
  tech_jobs_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO tech_jobs_count FROM sofia.tech_jobs;
  SELECT COUNT(*) INTO jobs_final FROM sofia.jobs;

  RAISE NOTICE '✅ Migration Statistics:';
  RAISE NOTICE '- tech_jobs records: %', tech_jobs_count;
  RAISE NOTICE '- jobs records (final): %', jobs_final;
  RAISE NOTICE '- Expected minimum: ~9100 (after deduplication)';
END $$;

-- Step 7: Source breakdown
SELECT
  source,
  COUNT(*) as job_count,
  COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days
FROM sofia.jobs
GROUP BY source
ORDER BY job_count DESC;

-- Step 8: Verify NO DATA LOSS from tech_jobs
DO $$
DECLARE
  missing_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO missing_count
  FROM sofia.tech_jobs tj
  WHERE NOT EXISTS (
    SELECT 1 FROM sofia.jobs j
    WHERE LOWER(TRIM(j.title)) = LOWER(TRIM(tj.title))
    AND LOWER(TRIM(j.company)) = LOWER(TRIM(tj.company))
    AND DATE(j.posted_date) = DATE(tj.posted_date)
  );

  IF missing_count > 0 THEN
    RAISE WARNING '⚠️  WARNING: % records from tech_jobs are missing in jobs!', missing_count;
  ELSE
    RAISE NOTICE '✅ SUCCESS: All tech_jobs records successfully migrated (NO DATA LOSS)';
  END IF;
END $$;

COMMENT ON COLUMN sofia.jobs.source IS 'Data source: greenhouse, adzuna, usajobs, remoteok, etc. (migrated from tech_jobs.platform)';
