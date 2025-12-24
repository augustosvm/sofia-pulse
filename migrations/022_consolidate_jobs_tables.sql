-- Migration: Consolidate Jobs Tables (tech_jobs → jobs)
-- Purpose: Merge tech_jobs into jobs (preserving 3,570 unique records)
-- Overlap: 113 duplicates
-- Result: ~9,000 total jobs (5,533 + 3,570 - 113)

-- Step 1: Ensure jobs table has all necessary columns from tech_jobs
-- (Most columns already exist, but check for missing ones)

ALTER TABLE sofia.jobs
ADD COLUMN IF NOT EXISTS has_relocation BOOLEAN DEFAULT false;

-- Update source column to NOT NULL with default
ALTER TABLE sofia.jobs
ALTER COLUMN source SET DEFAULT 'unknown';

UPDATE sofia.jobs
SET source = 'unknown'
WHERE source IS NULL OR source = '';

-- Step 2: Create unique constraint for deduplication
-- This prevents inserting duplicates based on title, company, and posted_date
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_unique_posting
ON sofia.jobs (
  LOWER(TRIM(title)),
  LOWER(TRIM(company)),
  DATE(posted_date)
);

-- Step 3: Migrate data from tech_jobs to jobs
-- Map tech_jobs columns to jobs columns
-- IMPORTANT: This preserves ALL 3,570 unique records without data loss

INSERT INTO sofia.jobs (
  -- Identifiers
  job_id,
  title,
  company,
  company_size,
  company_url,

  -- Location
  location,
  city,
  country,
  country_id,
  city_id,

  -- Job details
  description,
  employment_type,
  seniority_level,
  remote_type,
  experience_years_min,
  experience_years_max,

  -- Salary
  salary_min,
  salary_max,
  salary_currency,
  salary_period,

  -- Benefits
  has_health_insurance,
  has_equity,
  visa_sponsorship,
  has_relocation,

  -- Skills and requirements
  skills_required,
  search_keyword,

  -- URLs
  url,

  -- Source and timestamps
  source, -- Map platform → source
  posted_date,
  collected_at,
  created_at,
  updated_at
)
SELECT
  -- Identifiers
  job_id,
  title,
  company,
  company_size,
  company_url,

  -- Location
  location,
  city,
  country,
  country_id,
  city_id,

  -- Job details
  description,
  employment_type,
  seniority_level,
  remote_type,
  experience_years_min,
  experience_years_max,

  -- Salary
  salary_min,
  salary_max,
  salary_currency,
  salary_period,

  -- Benefits
  has_health_insurance,
  has_equity,
  has_visa_sponsorship as visa_sponsorship,
  has_relocation,

  -- Skills and requirements
  skills_required,
  search_keyword,

  -- URLs
  url,

  -- Source and timestamps
  platform as source, -- CRITICAL: Map platform → source
  posted_date,
  collected_at,
  NOW() as created_at,
  NOW() as updated_at

FROM sofia.tech_jobs

-- Deduplication: Skip records that already exist in jobs
ON CONFLICT (LOWER(TRIM(title)), LOWER(TRIM(company)), DATE(posted_date))
DO UPDATE SET
  -- Update with newer data if tech_jobs has more complete information
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

-- Step 4: Add index on source for better query performance
CREATE INDEX IF NOT EXISTS idx_jobs_source ON sofia.jobs(source);

-- Step 5: Verify migration (count records)
DO $$
DECLARE
  jobs_before INTEGER;
  tech_jobs_count INTEGER;
  jobs_after INTEGER;
  unique_added INTEGER;
BEGIN
  -- Get counts
  SELECT COUNT(*) INTO tech_jobs_count FROM sofia.tech_jobs;
  SELECT COUNT(*) INTO jobs_after FROM sofia.jobs;

  RAISE NOTICE 'Migration Statistics:';
  RAISE NOTICE '- tech_jobs records: %', tech_jobs_count;
  RAISE NOTICE '- jobs records (after): %', jobs_after;
  RAISE NOTICE '- Expected minimum: % (5533 original + 3570 unique from tech_jobs)', 5533 + 3570;

  -- Source breakdown in jobs table
  FOR unique_added IN
    SELECT COUNT(*) FROM (
      SELECT source, COUNT(*) as count
      FROM sofia.jobs
      GROUP BY source
      ORDER BY count DESC
    ) s
  LOOP
    NULL;
  END LOOP;

  RAISE NOTICE 'Source breakdown in jobs table:';
END $$;

-- Show source breakdown
SELECT
  source,
  COUNT(*) as job_count,
  COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
  MAX(posted_date) as latest_posting
FROM sofia.jobs
GROUP BY source
ORDER BY job_count DESC;

-- Step 6: Verify NO DATA LOSS
-- Check that all unique records from tech_jobs are now in jobs
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
    RAISE NOTICE '✅ SUCCESS: All tech_jobs records successfully migrated to jobs (NO DATA LOSS)';
  END NOTICE;
END $$;

-- Step 7: After verification, tech_jobs can be dropped with:
-- DROP TABLE sofia.tech_jobs;
-- (Keep commented until manual verification is complete)

COMMENT ON COLUMN sofia.jobs.source IS 'Data source: greenhouse, adzuna, usajobs, remoteok, etc. (migrated from tech_jobs.platform)';
