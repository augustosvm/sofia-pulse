-- ============================================================
-- CRIAR TABELA ORGANIZATIONS - Versão Simplificada
-- ============================================================

-- Criar tabela organizations (se institutions existir, renomear)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='sofia' AND table_name='institutions') THEN
        ALTER TABLE sofia.institutions RENAME TO organizations;
    END IF;
END $$;

-- Criar se não existir
CREATE TABLE IF NOT EXISTS sofia.organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    normalized_name VARCHAR(500) UNIQUE NOT NULL,
    legal_name VARCHAR(500),
    trade_name VARCHAR(500),
    tax_id VARCHAR(50),
    type VARCHAR(100),
    type_id INTEGER REFERENCES sofia.types(id),
    industry VARCHAR(100),
    industry_id INTEGER REFERENCES sofia.types(id),
    size VARCHAR(50),
    founded_year INTEGER,
    employee_count INTEGER,
    website_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    description TEXT,
    source_id INTEGER REFERENCES sofia.sources(id),
    country_id INTEGER REFERENCES sofia.countries(id),
    city_id INTEGER REFERENCES sofia.cities(id),
    active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_organizations_normalized_name ON sofia.organizations(normalized_name);
CREATE INDEX IF NOT EXISTS idx_organizations_type_id ON sofia.organizations(type_id);
CREATE INDEX IF NOT EXISTS idx_organizations_industry_id ON sofia.organizations(industry_id);
CREATE INDEX IF NOT EXISTS idx_organizations_source ON sofia.organizations(source_id);
CREATE INDEX IF NOT EXISTS idx_organizations_country ON sofia.organizations(country_id);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON sofia.organizations(active);

-- Popular com dados de research institutions
INSERT INTO sofia.organizations (name, normalized_name, type, source_id, metadata)
SELECT DISTINCT
    institution,
    LOWER(TRIM(REGEXP_REPLACE(institution, '\s+', ' ', 'g'))),
    CASE 
        WHEN institution ILIKE '%university%' OR institution ILIKE '%universidade%' THEN 'university'
        WHEN institution ILIKE '%hospital%' THEN 'hospital'
        ELSE 'research_center'
    END,
    (SELECT id FROM sofia.sources WHERE name = 'openalex' LIMIT 1),
    jsonb_build_object('migrated_from', 'brazil_research_institutions')
FROM sofia.brazil_research_institutions
WHERE institution IS NOT NULL
ON CONFLICT (normalized_name) DO NOTHING;

INSERT INTO sofia.organizations (name, normalized_name, type, source_id, metadata)
SELECT DISTINCT
    institution,
    LOWER(TRIM(REGEXP_REPLACE(institution, '\s+', ' ', 'g'))),
    CASE 
        WHEN institution ILIKE '%university%' THEN 'university'
        WHEN institution ILIKE '%hospital%' THEN 'hospital'
        ELSE 'research_center'
    END,
    (SELECT id FROM sofia.sources WHERE name = 'openalex' LIMIT 1),
    jsonb_build_object('migrated_from', 'global_research_institutions')
FROM sofia.global_research_institutions
WHERE institution IS NOT NULL
ON CONFLICT (normalized_name) DO NOTHING;

-- Atualizar type_id baseado em type
UPDATE sofia.organizations o
SET type_id = t.id
FROM sofia.types t
WHERE o.type = t.normalized_name
AND t.category = 'organization_type'
AND o.type_id IS NULL;

-- Verificar
SELECT 'organizations criada' AS status, COUNT(*) AS total FROM sofia.organizations;
SELECT 'por tipo' AS info, type, COUNT(*) AS count 
FROM sofia.organizations 
GROUP BY type 
ORDER BY count DESC 
LIMIT 5;
