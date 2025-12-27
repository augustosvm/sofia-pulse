-- ============================================================================
-- Migration 042: Add organization_id to Priority Tables
-- ============================================================================
-- Adds organization_id foreign key to:
-- 1. funding_rounds (7,097 records)
-- 2. space_industry (6,500 records)
-- 3. tech_jobs (3,675 records)
-- ============================================================================

-- 1. funding_rounds
ALTER TABLE sofia.funding_rounds
ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);

CREATE INDEX IF NOT EXISTS idx_funding_rounds_organization_id
ON sofia.funding_rounds(organization_id);

COMMENT ON COLUMN sofia.funding_rounds.organization_id IS
'Links to normalized organizations table. Populated from company_name field.';

-- 2. space_industry
ALTER TABLE sofia.space_industry
ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);

CREATE INDEX IF NOT EXISTS idx_space_industry_organization_id
ON sofia.space_industry(organization_id);

COMMENT ON COLUMN sofia.space_industry.organization_id IS
'Links to normalized organizations table. Populated from company field.';

-- 3. tech_jobs
ALTER TABLE sofia.tech_jobs
ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES sofia.organizations(id);

CREATE INDEX IF NOT EXISTS idx_tech_jobs_organization_id
ON sofia.tech_jobs(organization_id);

COMMENT ON COLUMN sofia.tech_jobs.organization_id IS
'Links to normalized organizations table. Populated from company field.';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 042 complete: organization_id columns added to 3 priority tables';
END $$;
