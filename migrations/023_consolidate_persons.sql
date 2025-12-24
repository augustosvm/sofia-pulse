-- ============================================================================
-- Migration 023: Consolidate Persons Table
-- ============================================================================
-- Adds 'type' column to persons and consolidates with authors table
-- ZERO DATA LOSS: All existing data preserved

BEGIN;

-- ============================================================================
-- 1. ADD TYPE COLUMN TO PERSONS
-- ============================================================================

ALTER TABLE sofia.persons
ADD COLUMN IF NOT EXISTS type VARCHAR(50);

-- Set default type for existing records based on data
UPDATE sofia.persons
SET type = CASE
  WHEN total_papers > 0 THEN 'researcher'
  ELSE 'person'
END
WHERE type IS NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_persons_type ON sofia.persons(type);

-- ============================================================================
-- 2. VERIFY OVERLAP BETWEEN AUTHORS AND PERSONS
-- ============================================================================

-- Create temp table to identify duplicates
CREATE TEMP TABLE author_person_overlap AS
SELECT
  a.id as author_id,
  p.id as person_id,
  a.full_name as author_name,
  p.full_name as person_name
FROM sofia.authors a
JOIN sofia.persons p ON LOWER(TRIM(a.full_name)) = LOWER(TRIM(p.full_name));

-- Summary of overlap
SELECT
  COUNT(DISTINCT author_id) as overlapping_authors,
  COUNT(DISTINCT person_id) as overlapping_persons
FROM author_person_overlap;

-- ============================================================================
-- 3. MIGRATE UNIQUE AUTHORS TO PERSONS
-- ============================================================================

-- Insert authors that DON'T exist in persons yet
INSERT INTO sofia.persons (
  full_name,
  normalized_name,
  orcid_id,
  h_index,
  total_citations,
  total_papers,
  gender,
  type,
  data_sources,
  first_seen,
  last_updated
)
SELECT
  a.full_name,
  LOWER(TRIM(REGEXP_REPLACE(a.full_name, '[^a-zA-Z0-9 ]', '', 'g'))) as normalized_name,
  a.orcid,
  COALESCE(a.h_index, 0),
  COALESCE(a.citation_count, 0),
  0 as total_papers, -- Will be calculated from paper_authors
  CASE
    WHEN a.detected_gender = 'male' THEN 'M'
    WHEN a.detected_gender = 'female' THEN 'F'
    ELSE NULL
  END as gender,
  'author' as type,
  ARRAY['authors_table'] as data_sources,
  NOW() as first_seen,
  NOW() as last_updated
FROM sofia.authors a
WHERE NOT EXISTS (
  SELECT 1 FROM sofia.persons p
  WHERE LOWER(TRIM(a.full_name)) = LOWER(TRIM(p.full_name))
)
ON CONFLICT (normalized_name) DO UPDATE SET
  orcid_id = COALESCE(EXCLUDED.orcid_id, sofia.persons.orcid_id),
  h_index = GREATEST(COALESCE(EXCLUDED.h_index, 0), COALESCE(sofia.persons.h_index, 0)),
  total_citations = GREATEST(COALESCE(EXCLUDED.total_citations, 0), COALESCE(sofia.persons.total_citations, 0)),
  gender = COALESCE(EXCLUDED.gender, sofia.persons.gender),
  data_sources = array_cat(sofia.persons.data_sources, EXCLUDED.data_sources),
  last_updated = NOW();

-- ============================================================================
-- 4. CREATE UNIQUE CONSTRAINT ON NORMALIZED_NAME
-- ============================================================================

-- First, ensure normalized_name is filled for all records
UPDATE sofia.persons
SET normalized_name = LOWER(TRIM(REGEXP_REPLACE(full_name, '[^a-zA-Z0-9 ]', '', 'g')))
WHERE normalized_name IS NULL;

-- Create unique constraint (will fail if duplicates exist)
-- If it fails, we'll need to deduplicate first
DO $$
BEGIN
  ALTER TABLE sofia.persons
  ADD CONSTRAINT persons_normalized_name_unique UNIQUE (normalized_name);
EXCEPTION
  WHEN duplicate_key THEN
    RAISE NOTICE 'Unique constraint already exists or duplicates found';
END $$;

-- ============================================================================
-- 5. STATISTICS
-- ============================================================================

-- Final counts
SELECT
  'persons' as table_name,
  COUNT(*) as total_records,
  COUNT(DISTINCT type) as unique_types,
  array_agg(DISTINCT type) as types
FROM sofia.persons

UNION ALL

SELECT
  'authors' as table_name,
  COUNT(*) as total_records,
  0 as unique_types,
  ARRAY['will be deprecated'] as types
FROM sofia.authors;

-- Count by type
SELECT
  type,
  COUNT(*) as count,
  COUNT(CASE WHEN orcid_id IS NOT NULL THEN 1 END) as with_orcid,
  COUNT(CASE WHEN country IS NOT NULL THEN 1 END) as with_country,
  COUNT(CASE WHEN primary_affiliation IS NOT NULL THEN 1 END) as with_affiliation
FROM sofia.persons
GROUP BY type
ORDER BY count DESC;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify no data loss
SELECT
  'Original authors' as source,
  245965 as expected_count,
  (SELECT COUNT(*) FROM sofia.authors) as actual_count;

SELECT
  'Persons after migration' as source,
  'Should be ~257k (130k + 126k new)' as expected_range,
  (SELECT COUNT(*) FROM sofia.persons) as actual_count;
