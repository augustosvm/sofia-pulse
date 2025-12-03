-- Migration: Fix NIH Grants VARCHAR Limits
-- Date: 2025-12-03
-- Purpose: Increase VARCHAR limits to accommodate real NIH API data
-- Issue: project_number and other fields were too small (50 chars) causing errors

-- Increase VARCHAR limits for nih_grants table
ALTER TABLE nih_grants
  ALTER COLUMN project_number TYPE VARCHAR(150),
  ALTER COLUMN principal_investigator TYPE VARCHAR(500),
  ALTER COLUMN organization TYPE VARCHAR(500),
  ALTER COLUMN city TYPE VARCHAR(200),
  ALTER COLUMN state TYPE VARCHAR(100),
  ALTER COLUMN country TYPE VARCHAR(200),
  ALTER COLUMN nih_institute TYPE VARCHAR(150),
  ALTER COLUMN funding_mechanism TYPE VARCHAR(100),
  ALTER COLUMN research_area TYPE VARCHAR(500);

-- Add comment explaining the change
COMMENT ON TABLE nih_grants IS 'NIH grants data - schema updated 2025-12-03 to fix VARCHAR limits';
