-- Migration: Consolidate Research Papers (3 tables → 1 unified table)
-- Purpose: Merge arxiv_ai_papers, openalex_papers, bdtd_theses → research_papers
-- Total: ~7,100 records

-- Step 1: Create unified research_papers table
CREATE TABLE IF NOT EXISTS sofia.research_papers (
  id SERIAL PRIMARY KEY,

  -- Universal fields
  title TEXT NOT NULL,
  abstract TEXT,
  authors TEXT[], -- Array of author names
  keywords TEXT[], -- Array of keywords/concepts
  publication_date DATE,
  publication_year INTEGER,

  -- Source-specific IDs
  source VARCHAR(50) NOT NULL, -- arxiv, openalex, bdtd
  source_id VARCHAR(255) NOT NULL, -- arxiv_id, openalex_id, thesis_id
  doi VARCHAR(255),

  -- Categories and classification
  primary_category VARCHAR(100),
  categories TEXT[], -- Array of categories/concepts
  area TEXT[], -- Research area (for theses)

  -- URLs and access
  pdf_url TEXT,
  journal VARCHAR(255),
  publisher VARCHAR(255),
  is_open_access BOOLEAN DEFAULT false,

  -- Academic metadata
  university VARCHAR(255), -- For theses
  program VARCHAR(255), -- For theses
  degree_type VARCHAR(50), -- Masters, PhD, etc.
  language VARCHAR(10), -- en, pt, es, etc.

  -- Author details
  author_institutions TEXT[], -- Array of institutions
  author_countries TEXT[], -- Array of countries

  -- Impact metrics
  cited_by_count INTEGER DEFAULT 0,
  referenced_works_count INTEGER DEFAULT 0,
  is_breakthrough BOOLEAN DEFAULT false,

  -- Embeddings (for ML)
  title_embedding vector(768),
  abstract_embedding vector(768),

  -- Timestamps
  collected_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique constraint
  CONSTRAINT research_papers_unique UNIQUE (source, source_id)
);

-- Step 2: Create indexes
CREATE INDEX IF NOT EXISTS idx_research_papers_source ON sofia.research_papers(source);
CREATE INDEX IF NOT EXISTS idx_research_papers_publication_date ON sofia.research_papers(publication_date DESC);
CREATE INDEX IF NOT EXISTS idx_research_papers_publication_year ON sofia.research_papers(publication_year DESC);
CREATE INDEX IF NOT EXISTS idx_research_papers_primary_category ON sofia.research_papers(primary_category);
CREATE INDEX IF NOT EXISTS idx_research_papers_is_breakthrough ON sofia.research_papers(is_breakthrough);
CREATE INDEX IF NOT EXISTS idx_research_papers_doi ON sofia.research_papers(doi) WHERE doi IS NOT NULL;

-- GIN indexes for arrays
CREATE INDEX IF NOT EXISTS idx_research_papers_authors_gin ON sofia.research_papers USING gin(authors);
CREATE INDEX IF NOT EXISTS idx_research_papers_keywords_gin ON sofia.research_papers USING gin(keywords);
CREATE INDEX IF NOT EXISTS idx_research_papers_categories_gin ON sofia.research_papers USING gin(categories);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_research_papers_title_fts
ON sofia.research_papers
USING gin(to_tsvector('english', COALESCE(title, '')));

CREATE INDEX IF NOT EXISTS idx_research_papers_abstract_fts
ON sofia.research_papers
USING gin(to_tsvector('english', COALESCE(abstract, '')));

-- Step 3: Migrate data from arxiv_ai_papers (4,394 records)
INSERT INTO sofia.research_papers (
  title,
  abstract,
  authors,
  keywords,
  publication_date,
  publication_year,
  source,
  source_id,
  pdf_url,
  primary_category,
  categories,
  is_open_access,
  author_countries,
  is_breakthrough,
  title_embedding,
  abstract_embedding,
  collected_at
)
SELECT
  title,
  abstract,
  authors,
  keywords,
  published_date as publication_date,
  EXTRACT(YEAR FROM published_date)::int as publication_year,
  'arxiv' as source,
  arxiv_id as source_id,
  pdf_url,
  primary_category,
  categories,
  true as is_open_access, -- ArXiv is always open access
  author_countries,
  is_breakthrough,
  title_embedding,
  abstract_embedding,
  collected_at
FROM sofia.arxiv_ai_papers
ON CONFLICT (source, source_id)
DO UPDATE SET
  title = EXCLUDED.title,
  abstract = EXCLUDED.abstract,
  keywords = EXCLUDED.keywords,
  is_breakthrough = EXCLUDED.is_breakthrough,
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 4: Migrate data from openalex_papers (2,700 records)
INSERT INTO sofia.research_papers (
  title,
  abstract,
  authors,
  keywords,
  publication_date,
  publication_year,
  source,
  source_id,
  doi,
  primary_category,
  categories,
  is_open_access,
  journal,
  publisher,
  author_institutions,
  author_countries,
  cited_by_count,
  referenced_works_count,
  title_embedding,
  abstract_embedding,
  collected_at
)
SELECT
  title,
  abstract,
  authors,
  concepts as keywords,
  publication_date,
  publication_year,
  'openalex' as source,
  openalex_id as source_id,
  doi,
  primary_concept as primary_category,
  concepts as categories,
  is_open_access,
  journal,
  publisher,
  author_institutions,
  author_countries,
  cited_by_count,
  referenced_works_count,
  title_embedding,
  abstract_embedding,
  collected_at
FROM sofia.openalex_papers
ON CONFLICT (source, source_id)
DO UPDATE SET
  title = EXCLUDED.title,
  abstract = EXCLUDED.abstract,
  cited_by_count = EXCLUDED.cited_by_count,
  referenced_works_count = EXCLUDED.referenced_works_count,
  is_open_access = EXCLUDED.is_open_access,
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 5: Migrate data from bdtd_theses (10 records)
INSERT INTO sofia.research_papers (
  title,
  abstract,
  authors,
  keywords,
  publication_year,
  source,
  source_id,
  pdf_url,
  area,
  university,
  program,
  degree_type,
  language,
  is_open_access,
  collected_at
)
SELECT
  title,
  abstract,
  CASE WHEN author IS NOT NULL THEN ARRAY[author] ELSE NULL END as authors,
  keywords,
  publication_year,
  'bdtd' as source,
  thesis_id as source_id,
  pdf_url,
  area,
  university,
  program,
  degree_type,
  language,
  true as is_open_access, -- Brazilian theses are usually open access
  collected_at
FROM sofia.bdtd_theses
ON CONFLICT (source, source_id)
DO UPDATE SET
  title = EXCLUDED.title,
  abstract = EXCLUDED.abstract,
  university = EXCLUDED.university,
  program = EXCLUDED.program,
  degree_type = EXCLUDED.degree_type,
  collected_at = EXCLUDED.collected_at,
  updated_at = NOW();

-- Step 6: Add comments
COMMENT ON TABLE sofia.research_papers IS 'Unified table for all research papers from ArXiv, OpenAlex, and BDTD theses';
COMMENT ON COLUMN sofia.research_papers.source IS 'Data source: arxiv, openalex, bdtd';
COMMENT ON COLUMN sofia.research_papers.source_id IS 'Original ID from source (arxiv_id, openalex_id, thesis_id)';
COMMENT ON COLUMN sofia.research_papers.is_breakthrough IS 'Marked as breakthrough research (high impact/novelty)';
COMMENT ON COLUMN sofia.research_papers.cited_by_count IS 'Number of citations (OpenAlex data)';

-- Step 7: Create helper view for latest papers
CREATE OR REPLACE VIEW sofia.latest_research_papers AS
SELECT
  source,
  COUNT(*) as total_papers,
  COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
  COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) as last_90_days,
  COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '365 days' THEN 1 END) as last_year,
  COUNT(CASE WHEN is_breakthrough THEN 1 END) as breakthrough_count,
  AVG(cited_by_count) as avg_citations,
  MAX(publication_date) as latest_paper
FROM sofia.research_papers
GROUP BY source
ORDER BY total_papers DESC;

-- Step 8: Verify migration
DO $$
DECLARE
  total_count INTEGER;
  source_breakdown TEXT;
BEGIN
  SELECT COUNT(*) INTO total_count FROM sofia.research_papers;

  SELECT string_agg(source || ': ' || count::text, ', ')
  INTO source_breakdown
  FROM (
    SELECT source, COUNT(*) as count
    FROM sofia.research_papers
    GROUP BY source
    ORDER BY count DESC
  ) s;

  RAISE NOTICE 'Migration complete!';
  RAISE NOTICE 'Total records in research_papers: %', total_count;
  RAISE NOTICE 'Source breakdown: %', source_breakdown;
END $$;

-- Step 9: After verification, old tables can be dropped with:
-- DROP TABLE sofia.arxiv_ai_papers;
-- DROP TABLE sofia.openalex_papers;
-- DROP TABLE sofia.bdtd_theses;
-- (Keep commented until manual verification is complete)
