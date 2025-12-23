-- Migration: Add source column for data compliance
-- Purpose: Track data source/origin for all collectors (required for compliance and auditing)
-- Affects: funding_rounds, developer_tools, tech_conferences

-- Add source to funding_rounds
ALTER TABLE sofia.funding_rounds
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_funding_rounds_source ON sofia.funding_rounds(source);

COMMENT ON COLUMN sofia.funding_rounds.source IS 'Data source (e.g., yc-companies, producthunt) for compliance tracking';

-- Add source to developer_tools
ALTER TABLE sofia.developer_tools
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_developer_tools_source ON sofia.developer_tools(source);

COMMENT ON COLUMN sofia.developer_tools.source IS 'Data source (e.g., vscode-marketplace, jetbrains-marketplace) for compliance tracking';

-- Add source to tech_conferences
ALTER TABLE sofia.tech_conferences
ADD COLUMN IF NOT EXISTS source VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_tech_conferences_source ON sofia.tech_conferences(source);

COMMENT ON COLUMN sofia.tech_conferences.source IS 'Data source (e.g., confs-tech, meetup) for compliance tracking';
