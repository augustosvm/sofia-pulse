-- Migration 015: Add organization_id column
-- Replace metadata->>'org_id' with proper organization_id column
-- Date: 2026-02-02
-- Purpose: Make org_id a first-class column for better indexing and querying

-- Add organization_id column (nullable first for migration)
ALTER TABLE sofia.organizations
  ADD COLUMN IF NOT EXISTS organization_id VARCHAR(500);

-- Migrate existing data from metadata->>'org_id' to organization_id
UPDATE sofia.organizations
SET organization_id = metadata->>'org_id'
WHERE organization_id IS NULL
  AND metadata->>'org_id' IS NOT NULL;

-- For records without org_id in metadata, use normalized_name
UPDATE sofia.organizations
SET organization_id = normalized_name
WHERE organization_id IS NULL;

-- Make it NOT NULL and UNIQUE now that data is migrated
ALTER TABLE sofia.organizations
  ALTER COLUMN organization_id SET NOT NULL,
  ADD CONSTRAINT organizations_organization_id_unique UNIQUE (organization_id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_organization_id ON sofia.organizations(organization_id);

-- Add comment
COMMENT ON COLUMN sofia.organizations.organization_id IS 'Unique organization identifier from source (e.g., globalgiving-redcross, aicompanies-openai)';

-- Note: normalized_name can now be dropped in future migration if desired
-- since organization_id serves the same purpose but with better semantics
