-- Migration 025: Add organization_id to jobs table
-- Created: 2025-12-24
-- Purpose: Link jobs to normalized organizations table

-- ============================================================================
-- ADD ORGANIZATION_ID COLUMN
-- ============================================================================

-- Add organization_id column (nullable for backward compatibility)
ALTER TABLE sofia.jobs
ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id) ON DELETE SET NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_jobs_organization_id ON sofia.jobs(organization_id);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN sofia.jobs.organization_id IS 'Foreign key to sofia.organizations - normalized company reference';

-- ============================================================================
-- HELPER FUNCTION: get_or_create_organization
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.get_or_create_organization(
    p_company_name VARCHAR,
    p_company_url VARCHAR DEFAULT NULL,
    p_location VARCHAR DEFAULT NULL,
    p_country VARCHAR DEFAULT NULL,
    p_source VARCHAR DEFAULT 'jobs-collector'
) RETURNS INTEGER AS $$
DECLARE
    v_org_id INTEGER;
    v_unique_org_id VARCHAR;
    v_normalized_name VARCHAR;
BEGIN
    -- Skip if company name is empty, null, or generic
    IF p_company_name IS NULL OR
       TRIM(p_company_name) = '' OR
       LOWER(TRIM(p_company_name)) IN ('não informado', 'confidential', 'n/a', 'unknown', 'undisclosed') THEN
        RETURN NULL;
    END IF;

    -- Normalize company name for matching
    v_normalized_name := LOWER(TRIM(REGEXP_REPLACE(p_company_name, '[^a-zA-Z0-9\s]', '', 'g')));

    -- Try to find existing organization by name (fuzzy match)
    SELECT id INTO v_org_id
    FROM sofia.organizations
    WHERE LOWER(TRIM(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s]', '', 'g'))) = v_normalized_name
    LIMIT 1;

    -- If found, return existing ID
    IF v_org_id IS NOT NULL THEN
        RETURN v_org_id;
    END IF;

    -- Create new organization
    v_unique_org_id := 'job-' || md5(v_normalized_name);

    INSERT INTO sofia.organizations (
        org_id,
        name,
        type,
        website,
        location,
        country,
        source,
        metadata
    ) VALUES (
        v_unique_org_id,
        p_company_name,
        'employer', -- New type for hiring companies
        p_company_url,
        p_location,
        p_country,
        p_source,
        jsonb_build_object('source', 'jobs_collector')
    )
    ON CONFLICT (org_id) DO UPDATE SET
        last_updated_at = NOW(),
        website = COALESCE(EXCLUDED.website, sofia.organizations.website),
        location = COALESCE(EXCLUDED.location, sofia.organizations.location),
        country = COALESCE(EXCLUDED.country, sofia.organizations.country)
    RETURNING id INTO v_org_id;

    RETURN v_org_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS ON FUNCTION
-- ============================================================================

COMMENT ON FUNCTION sofia.get_or_create_organization IS
'Finds or creates an organization record. Returns organization_id or NULL for generic/unknown companies.
Usage: SELECT sofia.get_or_create_organization(''OpenAI'', ''https://openai.com'', ''San Francisco'', ''USA'', ''github-jobs'');';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

/*
-- Example 1: Create/find organization and link to job
DO $$
DECLARE
    v_org_id INTEGER;
BEGIN
    v_org_id := sofia.get_or_create_organization(
        'OpenAI',
        'https://openai.com',
        'San Francisco, CA',
        'USA',
        'github-jobs'
    );

    -- Link to job
    UPDATE sofia.jobs
    SET organization_id = v_org_id
    WHERE company = 'OpenAI' AND organization_id IS NULL;
END $$;

-- Example 2: Query jobs by organization
SELECT
    j.title,
    o.name as company_name,
    o.country,
    o.website,
    j.posted_date
FROM sofia.jobs j
LEFT JOIN sofia.organizations o ON j.organization_id = o.id
WHERE o.type = 'employer'
ORDER BY j.posted_date DESC
LIMIT 10;

-- Example 3: Count jobs by organization
SELECT
    o.name,
    o.country,
    COUNT(j.id) as job_count
FROM sofia.organizations o
LEFT JOIN sofia.jobs j ON o.id = j.organization_id
WHERE o.type = 'employer'
GROUP BY o.name, o.country
ORDER BY job_count DESC
LIMIT 20;
*/
