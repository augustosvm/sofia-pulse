-- Migration 016: Create Organizations Table
-- Created: 2025-12-20
-- Purpose: Unified table for all types of organizations (AI Companies, NGOs, Universities, Startups, etc.)

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.organizations (
  id SERIAL PRIMARY KEY,
  org_id VARCHAR(200) UNIQUE NOT NULL,  -- Unique ID: 'source-identifier' (ex: 'aicompanies-openai')

  -- Common fields
  name VARCHAR(300) NOT NULL,
  type VARCHAR(50) NOT NULL,  -- 'ai_company', 'ngo', 'university', 'startup', 'vc_firm'
  industry VARCHAR(100),
  location VARCHAR(300),
  city VARCHAR(200),
  country VARCHAR(100),
  country_code VARCHAR(3),
  founded_date DATE,
  website VARCHAR(500),
  description TEXT,

  -- Size/Scale
  employee_count INTEGER,
  revenue_range VARCHAR(50),  -- 'seed', '1M-10M', '10M-100M', '100M-1B', '1B+'

  -- Arrays for flexibility
  tags TEXT[],  -- ['AI', 'LLM', 'Research', 'Healthcare']
  sources TEXT[],  -- ['ai-companies-api', 'crunchbase', 'linkedin']

  -- Specific fields (JSONB for flexibility per type)
  metadata JSONB,  -- Type-specific fields:
                   -- AI Companies: { github_stars, models_developed, papers_count }
                   -- NGOs: { beneficiaries, donations_received, focus_areas }
                   -- Universities: { ranking, research_output, student_count }

  -- Tracking
  source VARCHAR(100) NOT NULL,  -- Primary source collector name
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  last_updated_at TIMESTAMPTZ DEFAULT NOW(),
  collected_at TIMESTAMPTZ DEFAULT NOW(),

  -- Indexes
  CONSTRAINT organizations_org_id_key UNIQUE (org_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_organizations_type ON sofia.organizations(type);
CREATE INDEX IF NOT EXISTS idx_organizations_country ON sofia.organizations(country);
CREATE INDEX IF NOT EXISTS idx_organizations_tags ON sofia.organizations USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_organizations_source ON sofia.organizations(source);
CREATE INDEX IF NOT EXISTS idx_organizations_metadata ON sofia.organizations USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_organizations_name_search ON sofia.organizations USING GIN(to_tsvector('english', name));

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE sofia.organizations IS 'Unified table for all organization types: AI companies, NGOs, universities, startups, VCs, etc.';
COMMENT ON COLUMN sofia.organizations.org_id IS 'Unique identifier: source-id (e.g., aicompanies-openai, ngo-redcross)';
COMMENT ON COLUMN sofia.organizations.type IS 'Organization type: ai_company, ngo, university, startup, vc_firm, etc.';
COMMENT ON COLUMN sofia.organizations.metadata IS 'Type-specific fields stored as JSONB for flexibility';
COMMENT ON COLUMN sofia.organizations.tags IS 'Searchable tags: AI, Healthcare, Education, etc.';
COMMENT ON COLUMN sofia.organizations.sources IS 'List of sources that mention this organization';

-- ============================================================================
-- SAMPLE USAGE
-- ============================================================================

/*
-- AI Company example:
INSERT INTO sofia.organizations (
  org_id, name, type, industry, location, country, website, description, tags, metadata, source
) VALUES (
  'aicompanies-openai',
  'OpenAI',
  'ai_company',
  'Artificial Intelligence',
  'San Francisco, CA',
  'USA',
  'https://openai.com',
  'AI research and deployment company',
  ARRAY['AI', 'LLM', 'Research'],
  '{"github_stars": 50000, "models": ["GPT-4", "DALL-E"], "papers_count": 100}'::jsonb,
  'ai-companies'
);

-- NGO example:
INSERT INTO sofia.organizations (
  org_id, name, type, industry, location, country, website, description, tags, metadata, source
) VALUES (
  'ngo-redcross',
  'International Red Cross',
  'ngo',
  'Humanitarian',
  'Geneva',
  'Switzerland',
  'https://icrc.org',
  'Humanitarian organization',
  ARRAY['Healthcare', 'Emergency', 'Global'],
  '{"beneficiaries": 100000000, "countries_active": 192, "volunteers": 450000}'::jsonb,
  'world-ngos'
);

-- Query examples:
SELECT name, type, country FROM sofia.organizations WHERE type = 'ai_company';
SELECT name, metadata->>'models' as models FROM sofia.organizations WHERE tags @> ARRAY['AI'];
SELECT name, country FROM sofia.organizations WHERE metadata->>'github_stars' IS NOT NULL ORDER BY (metadata->>'github_stars')::int DESC;
*/
