-- Migration: Normalize Entities (Authors, Countries, Organizations)
-- Purpose: Create normalized entity tables with FKs from research_papers
-- Date: 2025-12-09

-- Step 1: Create countries table
CREATE TABLE IF NOT EXISTS sofia.countries (
  country_id SERIAL PRIMARY KEY,
  country_code VARCHAR(2) UNIQUE, -- ISO 3166-1 alpha-2
  country_name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT countries_unique UNIQUE (country_name)
);

CREATE INDEX IF NOT EXISTS idx_countries_code ON sofia.countries(country_code);
CREATE INDEX IF NOT EXISTS idx_countries_name ON sofia.countries(country_name);

-- Step 2: Create organizations table
CREATE TABLE IF NOT EXISTS sofia.organizations (
  organization_id SERIAL PRIMARY KEY,
  organization_name VARCHAR(500) NOT NULL,
  organization_type VARCHAR(50), -- university, company, research_institute
  country_id INTEGER REFERENCES sofia.countries(country_id),
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT organizations_unique UNIQUE (organization_name)
);

CREATE INDEX IF NOT EXISTS idx_organizations_name ON sofia.organizations(organization_name);
CREATE INDEX IF NOT EXISTS idx_organizations_type ON sofia.organizations(organization_type);
CREATE INDEX IF NOT EXISTS idx_organizations_country ON sofia.organizations(country_id);

-- Step 3: Create authors table
CREATE TABLE IF NOT EXISTS sofia.authors (
  author_id SERIAL PRIMARY KEY,
  author_name VARCHAR(500) NOT NULL,
  normalized_name VARCHAR(500), -- Nome normalizado (lowercase, sem acentos)
  orcid VARCHAR(19), -- ORCID identifier (0000-0001-2345-6789)
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT authors_unique UNIQUE (author_name)
);

CREATE INDEX IF NOT EXISTS idx_authors_name ON sofia.authors(author_name);
CREATE INDEX IF NOT EXISTS idx_authors_normalized ON sofia.authors(normalized_name);
CREATE INDEX IF NOT EXISTS idx_authors_orcid ON sofia.authors(orcid) WHERE orcid IS NOT NULL;

-- Step 4: Create paper_authors junction table (many-to-many)
CREATE TABLE IF NOT EXISTS sofia.paper_authors (
  paper_id INTEGER NOT NULL REFERENCES sofia.research_papers(id) ON DELETE CASCADE,
  author_id INTEGER NOT NULL REFERENCES sofia.authors(author_id) ON DELETE CASCADE,
  author_position INTEGER, -- Ordem do autor no paper
  PRIMARY KEY (paper_id, author_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_authors_paper ON sofia.paper_authors(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_authors_author ON sofia.paper_authors(author_id);
CREATE INDEX IF NOT EXISTS idx_paper_authors_position ON sofia.paper_authors(author_position);

-- Step 5: Create paper_countries junction table
CREATE TABLE IF NOT EXISTS sofia.paper_countries (
  paper_id INTEGER NOT NULL REFERENCES sofia.research_papers(id) ON DELETE CASCADE,
  country_id INTEGER NOT NULL REFERENCES sofia.countries(country_id) ON DELETE CASCADE,
  PRIMARY KEY (paper_id, country_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_countries_paper ON sofia.paper_countries(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_countries_country ON sofia.paper_countries(country_id);

-- Step 6: Create paper_organizations junction table
CREATE TABLE IF NOT EXISTS sofia.paper_organizations (
  paper_id INTEGER NOT NULL REFERENCES sofia.research_papers(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES sofia.organizations(organization_id) ON DELETE CASCADE,
  PRIMARY KEY (paper_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_organizations_paper ON sofia.paper_organizations(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_organizations_org ON sofia.paper_organizations(organization_id);

-- Step 7: Add organization_id FK to research_papers (for BDTD university)
ALTER TABLE sofia.research_papers 
ADD COLUMN IF NOT EXISTS primary_organization_id INTEGER REFERENCES sofia.organizations(organization_id);

CREATE INDEX IF NOT EXISTS idx_research_papers_org ON sofia.research_papers(primary_organization_id);

-- Step 8: Add comments
COMMENT ON TABLE sofia.countries IS 'Normalized countries (from author_countries)';
COMMENT ON TABLE sofia.organizations IS 'Normalized organizations (universities, institutions)';
COMMENT ON TABLE sofia.authors IS 'Normalized authors (from paper authors arrays)';
COMMENT ON TABLE sofia.paper_authors IS 'Many-to-many: papers ↔ authors';
COMMENT ON TABLE sofia.paper_countries IS 'Many-to-many: papers ↔ countries';
COMMENT ON TABLE sofia.paper_organizations IS 'Many-to-many: papers ↔ organizations';

-- Step 9: Insert common countries (seed data)
INSERT INTO sofia.countries (country_code, country_name) VALUES
  ('US', 'United States'),
  ('BR', 'Brazil'),
  ('GB', 'United Kingdom'),
  ('DE', 'Germany'),
  ('FR', 'France'),
  ('CN', 'China'),
  ('JP', 'Japan'),
  ('IN', 'India'),
  ('CA', 'Canada'),
  ('AU', 'Australia')
ON CONFLICT (country_name) DO NOTHING;

RAISE NOTICE 'Entity normalization tables created successfully!';
