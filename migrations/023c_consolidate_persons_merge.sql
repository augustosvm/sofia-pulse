-- ============================================================================
-- Migration 023c: Consolidate Persons (MERGE duplicates)
-- ============================================================================
-- EXECUTADO: 22 Dez 2025 - 00:15 UTC
-- RESULTADO: 130,934 → 222,454 pessoas (91,520 autores adicionados)

BEGIN;

-- 1. ADD TYPE COLUMN
ALTER TABLE sofia.persons ADD COLUMN IF NOT EXISTS type VARCHAR(50);

-- 2. Fill normalized_name
UPDATE sofia.persons
SET normalized_name = LOWER(TRIM(REGEXP_REPLACE(full_name, '[^a-zA-Z0-9 ]', '', 'g')))
WHERE normalized_name IS NULL OR normalized_name = '';

-- 3. Set type for existing records
UPDATE sofia.persons
SET type = 'researcher'
WHERE type IS NULL;

-- 4. Create index
CREATE INDEX IF NOT EXISTS idx_persons_type ON sofia.persons(type);
CREATE INDEX IF NOT EXISTS idx_persons_normalized_name ON sofia.persons(normalized_name);

-- 5. Insert unique authors (those NOT in persons)
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
SELECT DISTINCT ON (LOWER(TRIM(a.full_name)))
  a.full_name,
  LOWER(TRIM(REGEXP_REPLACE(a.full_name, '[^a-zA-Z0-9 ]', '', 'g'))) as normalized_name,
  a.orcid,
  COALESCE(a.h_index, 0),
  COALESCE(a.citation_count, 0),
  0 as total_papers,
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
ORDER BY LOWER(TRIM(a.full_name)), a.id;

COMMIT;

-- RESULTADO:
-- - researchers: 130,934 (dados originais do OpenAlex)
-- - authors: 91,520 (novos, da tabela authors)
-- - TOTAL: 222,454 pessoas físicas
