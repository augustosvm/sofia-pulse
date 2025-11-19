#!/bin/bash

echo "🔧 Fixing database schemas..."

PGPASSWORD="${DB_PASSWORD:-sofia123strong}" psql -h localhost -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" << 'SQL'

-- 1. Fix OpenAlex (VARCHAR(10) -> TEXT)
DROP TABLE IF EXISTS openalex_papers CASCADE;

CREATE TABLE openalex_papers (
  id SERIAL PRIMARY KEY,
  openalex_id VARCHAR(50) UNIQUE,
  doi VARCHAR(100),
  title TEXT NOT NULL,
  publication_date DATE,
  publication_year INT,
  authors TEXT[],
  author_institutions TEXT[],
  author_countries TEXT[],
  concepts TEXT[],
  primary_concept VARCHAR(255),
  cited_by_count INT DEFAULT 0,
  referenced_works_count INT DEFAULT 0,
  is_open_access BOOLEAN,
  journal VARCHAR(500),
  publisher VARCHAR(255),
  abstract TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_openalex_pub_year ON openalex_papers(publication_year DESC);
CREATE INDEX IF NOT EXISTS idx_openalex_cited_by ON openalex_papers(cited_by_count DESC);
CREATE INDEX IF NOT EXISTS idx_openalex_concepts ON openalex_papers USING GIN(concepts);
CREATE INDEX IF NOT EXISTS idx_openalex_countries ON openalex_papers USING GIN(author_countries);

-- 2. Fix PyPI Stats (same issue as NPM)
DROP TABLE IF EXISTS sofia.pypi_stats CASCADE;

CREATE TABLE sofia.pypi_stats (
  id SERIAL PRIMARY KEY,
  package_name VARCHAR(200) NOT NULL,
  downloads_month INT DEFAULT 0,
  version VARCHAR(50),
  description TEXT,
  keywords TEXT[],
  collected_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pypi_package_date ON sofia.pypi_stats(package_name, DATE(collected_at));
CREATE INDEX IF NOT EXISTS idx_pypi_package ON sofia.pypi_stats(package_name);
CREATE INDEX IF NOT EXISTS idx_pypi_downloads ON sofia.pypi_stats(downloads_month DESC);
CREATE INDEX IF NOT EXISTS idx_pypi_date ON sofia.pypi_stats(collected_at DESC);

-- 3. Re-run NPM migration (in case it wasn't applied correctly)
DROP TABLE IF EXISTS sofia.npm_stats CASCADE;

CREATE TABLE sofia.npm_stats (
  id SERIAL PRIMARY KEY,
  package_name VARCHAR(200) NOT NULL,
  downloads_day INT DEFAULT 0,
  downloads_week INT DEFAULT 0,
  downloads_month INT DEFAULT 0,
  version VARCHAR(50),
  description TEXT,
  keywords TEXT[],
  collected_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_npm_package_date ON sofia.npm_stats(package_name, DATE(collected_at));
CREATE INDEX IF NOT EXISTS idx_npm_package ON sofia.npm_stats(package_name);
CREATE INDEX IF NOT EXISTS idx_npm_downloads ON sofia.npm_stats(downloads_month DESC);
CREATE INDEX IF NOT EXISTS idx_npm_date ON sofia.npm_stats(collected_at DESC);

SQL

echo "✅ Database schemas fixed!"
