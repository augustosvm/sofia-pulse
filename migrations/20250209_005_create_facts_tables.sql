-- Migration: Create Facts Tables for Aggregations
-- Purpose: Create fact tables for normalized data aggregations
-- Date: 2025-12-09

-- Step 1: Create research monthly facts table
CREATE TABLE IF NOT EXISTS sofia.facts_research_monthly (
  id SERIAL PRIMARY KEY,

  -- Grain (unique combination)
  source VARCHAR(50) NOT NULL,              -- arxiv, openalex, bdtd
  publication_year INTEGER NOT NULL,
  publication_month INTEGER NOT NULL CHECK (publication_month BETWEEN 1 AND 12),

  -- Metrics (aggregated values)
  total_papers INTEGER DEFAULT 0,
  total_breakthrough INTEGER DEFAULT 0,
  total_open_access INTEGER DEFAULT 0,
  avg_citations NUMERIC(10, 2) DEFAULT 0,
  top_categories TEXT[],
  unique_authors INTEGER DEFAULT 0,
  unique_countries INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique constraint on grain
  CONSTRAINT facts_research_monthly_unique UNIQUE (source, publication_year, publication_month)
);

-- Step 2: Create indexes
CREATE INDEX IF NOT EXISTS idx_facts_research_monthly_source ON sofia.facts_research_monthly(source);
CREATE INDEX IF NOT EXISTS idx_facts_research_monthly_year ON sofia.facts_research_monthly(publication_year DESC);
CREATE INDEX IF NOT EXISTS idx_facts_research_monthly_month ON sofia.facts_research_monthly(publication_month);
CREATE INDEX IF NOT EXISTS idx_facts_research_monthly_year_month ON sofia.facts_research_monthly(publication_year DESC, publication_month DESC);

-- Step 3: Create tech packages weekly facts table (disabled for now)
CREATE TABLE IF NOT EXISTS sofia.facts_tech_weekly (
  id SERIAL PRIMARY KEY,

  -- Grain (unique combination)
  source VARCHAR(50) NOT NULL,              -- npm, pypi, github
  year INTEGER NOT NULL,
  week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 53),

  -- Metrics (aggregated values)
  total_packages INTEGER DEFAULT 0,
  total_downloads BIGINT DEFAULT 0,
  avg_stars NUMERIC(10, 2) DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique constraint on grain
  CONSTRAINT facts_tech_weekly_unique UNIQUE (source, year, week)
);

-- Step 4: Create indexes for tech weekly
CREATE INDEX IF NOT EXISTS idx_facts_tech_weekly_source ON sofia.facts_tech_weekly(source);
CREATE INDEX IF NOT EXISTS idx_facts_tech_weekly_year ON sofia.facts_tech_weekly(year DESC);
CREATE INDEX IF NOT EXISTS idx_facts_tech_weekly_week ON sofia.facts_tech_weekly(week);

-- Step 5: Add comments
COMMENT ON TABLE sofia.facts_research_monthly IS 'Monthly aggregation of research papers by source';
COMMENT ON COLUMN sofia.facts_research_monthly.source IS 'Data source: arxiv, openalex, bdtd';
COMMENT ON COLUMN sofia.facts_research_monthly.publication_year IS 'Publication year';
COMMENT ON COLUMN sofia.facts_research_monthly.publication_month IS 'Publication month (1-12)';
COMMENT ON COLUMN sofia.facts_research_monthly.total_papers IS 'Total number of papers published';
COMMENT ON COLUMN sofia.facts_research_monthly.total_breakthrough IS 'Number of breakthrough papers';
COMMENT ON COLUMN sofia.facts_research_monthly.total_open_access IS 'Number of open access papers';
COMMENT ON COLUMN sofia.facts_research_monthly.avg_citations IS 'Average citation count';
COMMENT ON COLUMN sofia.facts_research_monthly.top_categories IS 'Top categories for the month';
COMMENT ON COLUMN sofia.facts_research_monthly.unique_authors IS 'Number of unique authors';
COMMENT ON COLUMN sofia.facts_research_monthly.unique_countries IS 'Number of unique countries';

COMMENT ON TABLE sofia.facts_tech_weekly IS 'Weekly aggregation of tech packages by source';

-- Step 6: Create helper view for latest aggregations
CREATE OR REPLACE VIEW sofia.latest_facts_summary AS
SELECT
  'research_monthly' as fact_table,
  COUNT(*) as total_records,
  MIN(publication_year * 100 + publication_month) as earliest_period,
  MAX(publication_year * 100 + publication_month) as latest_period,
  SUM(total_papers) as total_aggregated_papers,
  MAX(updated_at) as last_updated
FROM sofia.facts_research_monthly
UNION ALL
SELECT
  'tech_weekly' as fact_table,
  COUNT(*) as total_records,
  MIN(year * 100 + week) as earliest_period,
  MAX(year * 100 + week) as latest_period,
  SUM(total_packages) as total_aggregated_papers,
  MAX(updated_at) as last_updated
FROM sofia.facts_tech_weekly;

-- Step 7: Verify tables created
DO $$
DECLARE
  research_count INTEGER;
  tech_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO research_count FROM sofia.facts_research_monthly;
  SELECT COUNT(*) INTO tech_count FROM sofia.facts_tech_weekly;

  RAISE NOTICE 'Facts tables created successfully!';
  RAISE NOTICE 'facts_research_monthly: % records', research_count;
  RAISE NOTICE 'facts_tech_weekly: % records', tech_count;
END $$;
