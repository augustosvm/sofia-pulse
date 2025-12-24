-- ============================================================
-- MIGRAÇÃO: Normalizar patents
-- Migra applicant VARCHAR -> company_id FK
-- ============================================================

-- 1. Adicionar coluna company_id
ALTER TABLE sofia.patents 
ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES sofia.companies(id);

-- 2. Popular companies master table
INSERT INTO sofia.companies (name, normalized_name, industry)
SELECT DISTINCT
    applicant,
    normalize_string(applicant),
    'patent_holder'
FROM sofia.patents
WHERE applicant IS NOT NULL
ON CONFLICT (normalized_name) DO NOTHING;

-- 3. Popular company_id
UPDATE sofia.patents p
SET company_id = c.id
FROM sofia.companies c
WHERE normalize_string(p.applicant) = c.normalized_name
AND p.company_id IS NULL;

-- 4. Criar índice
CREATE INDEX IF NOT EXISTS idx_patents_company_id ON sofia.patents(company_id);

-- 5. Verificação
SELECT 
    'patents normalization' AS status,
    COUNT(*) AS total_records,
    COUNT(company_id) AS with_company_id,
    ROUND(100.0 * COUNT(company_id) / NULLIF(COUNT(*), 0), 2) AS pct_normalized
FROM sofia.patents;

SELECT 
    'Unique companies' AS metric,
    COUNT(DISTINCT company_id) AS count
FROM sofia.patents
WHERE company_id IS NOT NULL;
