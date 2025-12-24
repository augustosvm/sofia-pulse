-- Migration 023: Add unique constraint on (job_id, platform)
-- This ensures each platform can only have one job with the same job_id

-- Check if constraint already exists before creating
DO $$
BEGIN
    -- Create unique index if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'sofia'
        AND tablename = 'jobs'
        AND indexname = 'idx_jobs_job_id_platform'
    ) THEN
        -- First, remove duplicates if any exist
        DELETE FROM sofia.jobs
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY job_id, platform ORDER BY collected_at DESC) as rn
                FROM sofia.jobs
                WHERE job_id IS NOT NULL AND platform IS NOT NULL
            ) t
            WHERE rn > 1
        );

        -- Now create the unique index
        CREATE UNIQUE INDEX idx_jobs_job_id_platform
        ON sofia.jobs (job_id, platform)
        WHERE job_id IS NOT NULL AND platform IS NOT NULL;

        RAISE NOTICE 'Created unique index idx_jobs_job_id_platform';
    ELSE
        RAISE NOTICE 'Index idx_jobs_job_id_platform already exists';
    END IF;
END $$;
