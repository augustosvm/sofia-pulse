-- Migration: Create Research Tables (Simplified - No pgvector)
-- Purpose: Create research_papers and source tables without vector columns for testing
-- Date: 2025-12-09

-- Step 1: Create unified research_papers table (simplified)
CREATE TABLE IF NOT EXISTS sofia.research_papers (
  id SERIAL PRIMARY KEY,

  -- Universal fields
  title TEXT NOT NULL,
  abstract TEXT,
  authors TEXT[],
  keywords TEXT[],
  publication_date DATE,
  publication_year INTEGER,

  -- Source-specific IDs
  source VARCHAR(50) NOT NULL,
  source_id VARCHAR(255) NOT NULL,
  doi VARCHAR(255),

  -- Categories and classification
  primary_category VARCHAR(100),
  categories TEXT[],
  area TEXT[],

  -- URLs and access
  pdf_url TEXT,
  journal VARCHAR(255),
  publisher VARCHAR(255),
  is_open_access BOOLEAN DEFAULT false,

  -- Academic metadata
  university VARCHAR(255),
  program VARCHAR(255),
  degree_type VARCHAR(50),
  language VARCHAR(10),

  -- Author details
  author_institutions TEXT[],
  author_countries TEXT[],

  -- Impact metrics
  cited_by_count INTEGER DEFAULT 0,
  referenced_works_count INTEGER DEFAULT 0,
  is_breakthrough BOOLEAN DEFAULT false,

  -- Timestamps
  collected_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Unique constraint
  CONSTRAINT research_papers_unique UNIQUE (source, source_id)
);

-- Step 2: Create source tables for testing

-- ArXiv papers
CREATE TABLE IF NOT EXISTS sofia.arxiv_ai_papers (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  abstract TEXT,
  authors TEXT[],
  keywords TEXT[],
  published_date DATE,
  arxiv_id VARCHAR(255) NOT NULL UNIQUE,
  pdf_url TEXT,
  primary_category VARCHAR(100),
  categories TEXT[],
  author_countries TEXT[],
  is_breakthrough BOOLEAN DEFAULT false,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- OpenAlex papers
CREATE TABLE IF NOT EXISTS sofia.openalex_papers (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  abstract TEXT,
  authors TEXT[],
  concepts TEXT[],
  publication_date DATE,
  publication_year INTEGER,
  openalex_id VARCHAR(255) NOT NULL UNIQUE,
  doi VARCHAR(255),
  primary_concept VARCHAR(100),
  is_open_access BOOLEAN DEFAULT false,
  journal VARCHAR(255),
  publisher VARCHAR(255),
  author_institutions TEXT[],
  author_countries TEXT[],
  cited_by_count INTEGER DEFAULT 0,
  referenced_works_count INTEGER DEFAULT 0,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- BDTD theses
CREATE TABLE IF NOT EXISTS sofia.bdtd_theses (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  abstract TEXT,
  author VARCHAR(255),
  keywords TEXT[],
  publication_year INTEGER,
  thesis_id VARCHAR(255) NOT NULL UNIQUE,
  pdf_url TEXT,
  area TEXT[],
  university VARCHAR(255),
  program VARCHAR(255),
  degree_type VARCHAR(50),
  language VARCHAR(10),
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Step 3: Insert sample data for testing

-- Sample ArXiv data
INSERT INTO sofia.arxiv_ai_papers (title, abstract, authors, keywords, published_date, arxiv_id, pdf_url, primary_category, categories, is_breakthrough)
VALUES
  ('Deep Learning for Computer Vision', 'A comprehensive study on deep learning techniques...', 
   ARRAY['John Smith', 'Jane Doe'], ARRAY['deep learning', 'computer vision'], 
   '2025-01-15', 'arxiv:2501.12345', 'https://arxiv.org/pdf/2501.12345', 
   'cs.CV', ARRAY['cs.CV', 'cs.AI'], false),
  ('Transformer Models in NLP', 'An analysis of transformer architectures...', 
   ARRAY['Alice Brown', 'Bob Johnson'], ARRAY['transformers', 'NLP'], 
   '2025-02-10', 'arxiv:2502.23456', 'https://arxiv.org/pdf/2502.23456', 
   'cs.CL', ARRAY['cs.CL', 'cs.AI'], true),
  ('Quantum Computing Breakthrough', 'A novel approach to quantum error correction...', 
   ARRAY['Carol White'], ARRAY['quantum computing', 'error correction'], 
   '2024-12-20', 'arxiv:2412.34567', 'https://arxiv.org/pdf/2412.34567', 
   'quant-ph', ARRAY['quant-ph'], true)
ON CONFLICT (arxiv_id) DO NOTHING;

-- Sample OpenAlex data
INSERT INTO sofia.openalex_papers (title, abstract, authors, concepts, publication_date, publication_year, openalex_id, doi, primary_concept, is_open_access, journal, cited_by_count)
VALUES
  ('Machine Learning in Healthcare', 'Application of ML techniques in medical diagnosis...', 
   ARRAY['Dr. Emily Chen', 'Dr. Michael Lee'], ARRAY['machine learning', 'healthcare'], 
   '2025-01-05', 2025, 'W1234567890', '10.1000/example.2025.001', 
   'Machine Learning', true, 'Journal of Medical AI', 45),
  ('Climate Change Impact Assessment', 'Analyzing the effects of climate change on biodiversity...', 
   ARRAY['Dr. Sarah Green'], ARRAY['climate change', 'biodiversity'], 
   '2024-11-30', 2024, 'W0987654321', '10.1000/example.2024.456', 
   'Environmental Science', true, 'Nature Climate', 78)
ON CONFLICT (openalex_id) DO NOTHING;

-- Sample BDTD data
INSERT INTO sofia.bdtd_theses (title, abstract, author, keywords, publication_year, thesis_id, university, program, degree_type, language)
VALUES
  ('Inteligência Artificial na Educação', 'Estudo sobre aplicações de IA no ensino...', 
   'Carlos Silva', ARRAY['inteligência artificial', 'educação'], 
   2024, 'BDTD-001', 'USP', 'Ciência da Computação', 'PhD', 'pt')
ON CONFLICT (thesis_id) DO NOTHING;

-- Step 4: Create indexes
CREATE INDEX IF NOT EXISTS idx_research_papers_source ON sofia.research_papers(source);
CREATE INDEX IF NOT EXISTS idx_research_papers_publication_date ON sofia.research_papers(publication_date DESC);
CREATE INDEX IF NOT EXISTS idx_research_papers_publication_year ON sofia.research_papers(publication_year DESC);
