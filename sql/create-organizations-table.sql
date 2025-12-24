-- ============================================================
-- ORGANIZATIONS (Pessoa Jurídica)
-- Renomeia institutions → organizations e expande
-- ============================================================

-- 1. Renomear tabela institutions para organizations
ALTER TABLE IF EXISTS sofia.institutions RENAME TO organizations;

-- 2. Adicionar/Atualizar campos para pessoa jurídica
ALTER TABLE sofia.organizations 
ADD COLUMN IF NOT EXISTS legal_name VARCHAR(500),  -- Razão social
ADD COLUMN IF NOT EXISTS trade_name VARCHAR(500),  -- Nome fantasia
ADD COLUMN IF NOT EXISTS tax_id VARCHAR(50),  -- CNPJ/EIN/VAT
ADD COLUMN IF NOT EXISTS type VARCHAR(100) NOT NULL DEFAULT 'company',  -- Tipo de organização
ADD COLUMN IF NOT EXISTS industry VARCHAR(100),  -- Setor/indústria
ADD COLUMN IF NOT EXISTS size VARCHAR(50),  -- 'startup', 'small', 'medium', 'large', 'enterprise'
ADD COLUMN IF NOT EXISTS founded_year INTEGER,
ADD COLUMN IF NOT EXISTS employee_count INTEGER,
ADD COLUMN IF NOT EXISTS revenue_usd BIGINT,
ADD COLUMN IF NOT EXISTS website_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sofia.sources(id),
ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id),
ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS metadata JSONB,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- 3. Atualizar nome para legal_name se ainda não existe
UPDATE sofia.organizations
SET legal_name = name
WHERE legal_name IS NULL AND name IS NOT NULL;

-- 4. Criar índices
CREATE INDEX IF NOT EXISTS idx_organizations_normalized_name ON sofia.organizations(normalized_name);
CREATE INDEX IF NOT EXISTS idx_organizations_type ON sofia.organizations(type);
CREATE INDEX IF NOT EXISTS idx_organizations_industry ON sofia.organizations(industry);
CREATE INDEX IF NOT EXISTS idx_organizations_tax_id ON sofia.organizations(tax_id);
CREATE INDEX IF NOT EXISTS idx_organizations_source ON sofia.organizations(source_id);
CREATE INDEX IF NOT EXISTS idx_organizations_country ON sofia.organizations(country_id);
CREATE INDEX IF NOT EXISTS idx_organizations_city ON sofia.organizations(city_id);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON sofia.organizations(active);

-- 5. Criar tipos de organização como ENUM (opcional, ou usar CHECK)
CREATE TYPE organization_type AS ENUM (
    'university',
    'research_center',
    'company',
    'startup',
    'government',
    'ngo',
    'foundation',
    'hospital',
    'school',
    'laboratory',
    'consortium',
    'other'
);

-- Não aplicar ENUM agora para não quebrar dados existentes
-- Apenas documentar os tipos válidos

-- 6. Popular organizations com dados de research institutions
INSERT INTO sofia.organizations (
    name, normalized_name, type, source_id, metadata
)
SELECT DISTINCT
    institution,
    normalize_string(institution),
    CASE 
        WHEN institution ILIKE '%university%' OR institution ILIKE '%universidade%' THEN 'university'
        WHEN institution ILIKE '%institute%' OR institution ILIKE '%instituto%' THEN 'research_center'
        WHEN institution ILIKE '%hospital%' THEN 'hospital'
        WHEN institution ILIKE '%school%' OR institution ILIKE '%escola%' THEN 'school'
        ELSE 'research_center'
    END,
    get_source_id('openalex'),
    jsonb_build_object('source_table', 'brazil_research_institutions')
FROM sofia.brazil_research_institutions
WHERE institution IS NOT NULL
ON CONFLICT (normalized_name) DO NOTHING;

INSERT INTO sofia.organizations (
    name, normalized_name, type, source_id, metadata
)
SELECT DISTINCT
    institution,
    normalize_string(institution),
    CASE 
        WHEN institution ILIKE '%university%' THEN 'university'
        WHEN institution ILIKE '%institute%' THEN 'research_center'
        WHEN institution ILIKE '%hospital%' THEN 'hospital'
        WHEN institution ILIKE '%school%' THEN 'school'
        WHEN institution ILIKE '%lab%' THEN 'laboratory'
        ELSE 'research_center'
    END,
    get_source_id('openalex'),
    jsonb_build_object('source_table', 'global_research_institutions')
FROM sofia.global_research_institutions
WHERE institution IS NOT NULL
ON CONFLICT (normalized_name) DO NOTHING;

-- 7. Atualizar company_id em persons para organization_id
ALTER TABLE sofia.persons 
RENAME COLUMN company_id TO organization_id;

-- Atualizar constraint
ALTER TABLE sofia.persons 
DROP CONSTRAINT IF EXISTS persons_company_id_fkey;

ALTER TABLE sofia.persons 
ADD CONSTRAINT persons_organization_id_fkey 
FOREIGN KEY (organization_id) REFERENCES sofia.organizations(id);

-- 8. Renomear companies para organizations também (se existir)
-- Migrar dados de companies para organizations
INSERT INTO sofia.organizations (
    name, normalized_name, type, industry, country_id, source_id, metadata
)
SELECT 
    name,
    normalized_name,
    'company',
    industry,
    country_id,
    source_id,
    metadata
FROM sofia.companies
ON CONFLICT (normalized_name) DO NOTHING;

-- 9. Criar função helper
CREATE OR REPLACE FUNCTION get_or_create_organization(
    org_name TEXT,
    org_type TEXT DEFAULT 'company',
    org_source_id INTEGER DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    org_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF org_name IS NULL OR TRIM(org_name) = '' THEN
        RETURN NULL;
    END IF;
    
    normalized := normalize_string(org_name);
    
    -- Buscar existente
    SELECT id INTO org_id_result
    FROM sofia.organizations
    WHERE normalized_name = normalized
    LIMIT 1;
    
    IF org_id_result IS NULL THEN
        -- Criar novo
        INSERT INTO sofia.organizations (name, normalized_name, type, source_id)
        VALUES (TRIM(org_name), normalized, org_type, org_source_id)
        ON CONFLICT (normalized_name) DO NOTHING
        RETURNING id INTO org_id_result;
        
        IF org_id_result IS NULL THEN
            SELECT id INTO org_id_result
            FROM sofia.organizations
            WHERE normalized_name = normalized
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN org_id_result;
END;
$$ LANGUAGE plpgsql;

-- 10. Trigger para updated_at
CREATE OR REPLACE FUNCTION update_organizations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER organizations_updated_at
    BEFORE UPDATE ON sofia.organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_organizations_updated_at();

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================

SELECT 
    'organizations table' AS status,
    COUNT(*) AS total,
    COUNT(CASE WHEN type = 'university' THEN 1 END) AS universities,
    COUNT(CASE WHEN type = 'research_center' THEN 1 END) AS research_centers,
    COUNT(CASE WHEN type = 'company' THEN 1 END) AS companies,
    COUNT(CASE WHEN type = 'startup' THEN 1 END) AS startups,
    COUNT(CASE WHEN type = 'government' THEN 1 END) AS government,
    COUNT(source_id) AS with_source,
    COUNT(country_id) AS with_country
FROM sofia.organizations;

SELECT 
    'organizations by type' AS report,
    type,
    COUNT(*) AS count
FROM sofia.organizations
GROUP BY type
ORDER BY count DESC;

SELECT 
    'Top 10 organizations' AS report,
    name,
    type,
    country_id
FROM sofia.organizations
ORDER BY id
LIMIT 10;
