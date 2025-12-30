-- Migration: Add UNIQUE constraint to job_id
-- Author: Sofia Pulse
-- Date: 2025-12-30
-- Description: Add unique constraint to job_id column for ON CONFLICT handling

-- Add unique constraint (ignoring if already exists)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'jobs_job_id_key'
  ) THEN
    ALTER TABLE sofia.jobs ADD CONSTRAINT jobs_job_id_key UNIQUE (job_id);
    RAISE NOTICE 'Added UNIQUE constraint to job_id';
  ELSE
    RAISE NOTICE 'UNIQUE constraint on job_id already exists';
  END IF;
END $$;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON sofia.jobs(job_id);

-- Comment
COMMENT ON COLUMN sofia.jobs.job_id IS 'Unique job identifier from source platform (e.g., catho-12345, linkedin-67890)';
