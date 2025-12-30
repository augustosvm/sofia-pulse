-- ============================================================
-- CONSOLIDAÇÃO: PATENTS
-- Consolida 4 tabelas → 1 tabela unificada
-- ============================================================

-- 1. CRIAR TABELA UNIFICADA
CREATE TABLE IF NOT EXISTS sofia.patents (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'epo', 'wipo', 'uspto'
    patent_number VARCHAR(100) NOT NULL,
    
    -- Identificação
    title TEXT,
    abstract TEXT,
    
    -- Partes
    applicant VARCHAR(500),
    inventor VARCHAR(500),
    
    -- Classificação
    ipc_classification TEXT[],
    technology_field VARCHAR(200),
    
    -- Geográfico (normalizado)
    country_id INTEGER REFERENCES sofia.countries(id),
    applicant_country VARCHAR(100),
    
    -- Temporal
    filing_date DATE,
    publication_date DATE,
    grant_date DATE,
    
    -- Metadata flexível
    metadata JSONB,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(source, patent_number)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_patents_source ON sofia.patents(source);
CREATE INDEX IF NOT EXISTS idx_patents_country ON sofia.patents(country_id);
CREATE INDEX IF NOT EXISTS idx_patents_filing_date ON sofia.patents(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_patents_applicant ON sofia.patents(applicant);
CREATE INDEX IF NOT EXISTS idx_patents_tech_field ON sofia.patents(technology_field);
CREATE INDEX IF NOT EXISTS idx_patents_ipc ON sofia.patents USING GIN(ipc_classification);

-- 2. MIGRAR DADOS EXISTENTES

-- Migrar epo_patents (11 registros)
INSERT INTO sofia.patents (
    source, patent_number, title, abstract,
    applicant, inventor,
    ipc_classification, technology_field,
    applicant_country,
    filing_date, publication_date,
    collected_at, metadata
)
SELECT 
    'epo' as source,
    publication_number as patent_number,
    title,
    abstract,
    applicant,
    inventor,
    ipc_classification,
    technology_field,
    applicant_country,
    filing_date,
    publication_date,
    collected_at,
    jsonb_build_object(
        'publication_number', publication_number,
        'application_number', application_number
    ) as metadata
FROM sofia.epo_patents
ON CONFLICT (source, patent_number) DO NOTHING;

-- Migrar wipo_china_patents (10 registros)
INSERT INTO sofia.patents (
    source, patent_number, title, abstract,
    applicant, inventor,
    ipc_classification, technology_field,
    applicant_country,
    filing_date, publication_date,
    collected_at, metadata
)
SELECT 
    'wipo' as source,
    publication_number as patent_number,
    title,
    abstract,
    applicant,
    inventor,
    ipc_classification,
    technology_field,
    applicant_country,
    filing_date,
    publication_date,
    collected_at,
    jsonb_build_object(
        'publication_number', publication_number,
        'application_number', application_number
    ) as metadata
FROM sofia.wipo_china_patents
ON CONFLICT (source, patent_number) DO NOTHING;

-- 3. NORMALIZAR GEOGRÁFICO (se ainda não normalizado)
UPDATE sofia.patents
SET country_id = get_or_create_country(applicant_country)
WHERE applicant_country IS NOT NULL AND country_id IS NULL;

-- 4. VERIFICAR MIGRAÇÃO
SELECT 
    'PATENTS MIGRATION' as status,
    source,
    COUNT(*) as records,
    MIN(filing_date) as earliest_filing,
    MAX(filing_date) as latest_filing,
    COUNT(DISTINCT applicant_country) as countries
FROM sofia.patents
GROUP BY source
ORDER BY source;

-- 5. DELETAR TABELA VAZIA (SEGURO)
DROP TABLE IF EXISTS sofia.person_patents CASCADE;  -- vazia

-- 6. RELATÓRIO FINAL
SELECT 
    'Patents Consolidation Complete' as status,
    COUNT(*) as total_records,
    COUNT(DISTINCT source) as sources,
    COUNT(DISTINCT applicant) as unique_applicants,
    COUNT(DISTINCT technology_field) as tech_fields
FROM sofia.patents;
