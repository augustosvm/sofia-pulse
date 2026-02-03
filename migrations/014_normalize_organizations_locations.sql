-- Migration 014: Normalize Organizations Locations
-- Add foreign key columns for city, country, state to organizations table
-- Date: 2026-02-02
-- Purpose: Replace string-based location storage with proper foreign keys

-- Add normalized location columns
ALTER TABLE sofia.organizations
  ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
  ADD COLUMN IF NOT EXISTS state_id INTEGER REFERENCES sofia.states(id),
  ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_country_id ON sofia.organizations(country_id);
CREATE INDEX IF NOT EXISTS idx_organizations_state_id ON sofia.organizations(state_id);
CREATE INDEX IF NOT EXISTS idx_organizations_city_id ON sofia.organizations(city_id);

-- Migrate existing data from metadata JSONB to normalized columns
-- This will match countries by common_name, iso_alpha2, or iso_alpha3
UPDATE sofia.organizations o
SET country_id = c.id
FROM sofia.countries c
WHERE country_id IS NULL
  AND (
    o.metadata->>'country' = c.common_name
    OR o.metadata->>'country_code' = c.iso_alpha2
    OR o.metadata->>'country_code' = c.iso_alpha3
    OR UPPER(o.metadata->>'country') = UPPER(c.common_name)
  );

-- Migrate states (match by name and country)
UPDATE sofia.organizations o
SET state_id = s.id
FROM sofia.states s
WHERE state_id IS NULL
  AND o.country_id = s.country_id
  AND (
    o.metadata->>'state' = s.name
    OR o.metadata->>'state' = s.code
  );

-- Migrate cities (match by name, state, and country)
UPDATE sofia.organizations o
SET city_id = ci.id
FROM sofia.cities ci
WHERE city_id IS NULL
  AND o.country_id = ci.country_id
  AND (o.state_id = ci.state_id OR o.state_id IS NULL)
  AND o.metadata->>'city' = ci.name;

-- Add comment
COMMENT ON COLUMN sofia.organizations.country_id IS 'Foreign key to sofia.countries';
COMMENT ON COLUMN sofia.organizations.state_id IS 'Foreign key to sofia.states';
COMMENT ON COLUMN sofia.organizations.city_id IS 'Foreign key to sofia.cities';
