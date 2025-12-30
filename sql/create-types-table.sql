-- ============================================================
-- TABELA TYPES - Centraliza TODOS os tipos do sistema
-- Substitui VARCHAR types por FK normalizados
-- ============================================================

CREATE TABLE IF NOT EXISTS sofia.types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    normalized_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,  -- qual entidade usa este tipo
    description TEXT,
    parent_id INTEGER REFERENCES sofia.types(id),  -- hierarquia
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_types_normalized_name ON sofia.types(normalized_name);
CREATE INDEX IF NOT EXISTS idx_types_category ON sofia.types(category);
CREATE INDEX IF NOT EXISTS idx_types_parent ON sofia.types(parent_id);
CREATE INDEX IF NOT EXISTS idx_types_active ON sofia.types(active);

-- ============================================================
-- POPULAR TYPES INICIAIS
-- ============================================================

INSERT INTO sofia.types (name, normalized_name, category, description, display_order) VALUES

-- Organization Types
('University', 'university', 'organization_type', 'Universidade / University', 10),
('Research Center', 'research_center', 'organization_type', 'Centro de Pesquisa', 20),
('Company', 'company', 'organization_type', 'Empresa', 30),
('Startup', 'startup', 'organization_type', 'Startup', 40),
('Government', 'government', 'organization_type', 'Órgão Governamental', 50),
('NGO', 'ngo', 'organization_type', 'ONG / Non-Profit', 60),
('Foundation', 'foundation', 'organization_type', 'Fundação', 70),
('Hospital', 'hospital', 'organization_type', 'Hospital', 80),
('School', 'school', 'organization_type', 'Escola', 90),
('Laboratory', 'laboratory', 'organization_type', 'Laboratório', 100),

-- Person Roles
('Researcher', 'researcher', 'person_role', 'Pesquisador / Researcher', 10),
('Inventor', 'inventor', 'person_role', 'Inventor', 20),
('Developer', 'developer', 'person_role', 'Desenvolvedor', 30),
('Author', 'author', 'person_role', 'Autor', 40),
('CEO', 'ceo', 'person_role', 'CEO / Diretor Executivo', 50),
('Founder', 'founder', 'person_role', 'Fundador', 60),
('CTO', 'cto', 'person_role', 'CTO / Diretor de Tecnologia', 70),
('Engineer', 'engineer', 'person_role', 'Engenheiro', 80),
('Scientist', 'scientist', 'person_role', 'Cientista', 90),

-- Source Categories
('API', 'api', 'source_category', 'API', 10),
('Scraper', 'scraper', 'source_category', 'Web Scraper', 20),
('Database', 'database', 'source_category', 'Database', 30),
('File', 'file', 'source_category', 'File Import', 40),
('Manual', 'manual', 'source_category', 'Manual Entry', 50),

-- Data Types
('Papers', 'papers', 'data_type', 'Academic Papers', 10),
('Patents', 'patents', 'data_type', 'Patents', 20),
('Jobs', 'jobs', 'data_type', 'Job Postings', 30),
('Trends', 'trends', 'data_type', 'Tech Trends', 40),
('Posts', 'posts', 'data_type', 'Community Posts', 50),
('Funding', 'funding', 'data_type', 'Funding Rounds', 60),

-- Trend Types
('Repository', 'repository', 'trend_type', 'GitHub Repository', 10),
('Package', 'package', 'trend_type', 'Package (npm, pypi)', 20),
('Tag', 'tag', 'trend_type', 'StackOverflow Tag', 30),
('Topic', 'topic', 'trend_type', 'Topic / Subject', 40),

-- Organization Sizes
('Startup', 'startup', 'organization_size', '1-10 employees', 10),
('Small', 'small', 'organization_size', '11-50 employees', 20),
('Medium', 'medium', 'organization_size', '51-200 employees', 30),
('Large', 'large', 'organization_size', '201-1000 employees', 40),
('Enterprise', 'enterprise', 'organization_size', '1000+ employees', 50),

-- Industries
('Technology', 'technology', 'industry', 'Technology / Software', 10),
('Healthcare', 'healthcare', 'industry', 'Healthcare / Medical', 20),
('Finance', 'finance', 'industry', 'Finance / Fintech', 30),
('Education', 'education', 'industry', 'Education / EdTech', 40),
('E-commerce', 'ecommerce', 'industry', 'E-commerce / Retail', 50),
('Energy', 'energy', 'industry', 'Energy / CleanTech', 60),
('Manufacturing', 'manufacturing', 'industry', 'Manufacturing', 70),
('Agriculture', 'agriculture', 'industry', 'Agriculture / AgTech', 80)

ON CONFLICT (normalized_name) DO NOTHING;

-- ============================================================
-- FUNÇÕES HELPER
-- ============================================================

-- Get type ID by name and category
CREATE OR REPLACE FUNCTION get_type_id(
    type_name TEXT,
    type_category TEXT
)
RETURNS INTEGER AS $$
DECLARE
    type_id_result INTEGER;
BEGIN
    SELECT id INTO type_id_result
    FROM sofia.types
    WHERE normalized_name = normalize_string(type_name)
      AND category = type_category
      AND active = true
    LIMIT 1;
    
    RETURN type_id_result;
END;
$$ LANGUAGE plpgsql;

-- Get or create type
CREATE OR REPLACE FUNCTION get_or_create_type(
    type_name TEXT,
    type_category TEXT,
    type_description TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    type_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF type_name IS NULL OR TRIM(type_name) = '' THEN
        RETURN NULL;
    END IF;
    
    normalized := normalize_string(type_name);
    
    SELECT id INTO type_id_result
    FROM sofia.types
    WHERE normalized_name = normalized
      AND category = type_category
    LIMIT 1;
    
    IF type_id_result IS NULL THEN
        INSERT INTO sofia.types (name, normalized_name, category, description)
        VALUES (TRIM(type_name), normalized, type_category, type_description)
        ON CONFLICT (normalized_name) DO NOTHING
        RETURNING id INTO type_id_result;
        
        IF type_id_result IS NULL THEN
            SELECT id INTO type_id_result
            FROM sofia.types
            WHERE normalized_name = normalized
              AND category = type_category
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN type_id_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- MIGRAR TABELAS PARA USAR type_id
-- ============================================================

-- 1. Organizations: type VARCHAR → type_id FK
ALTER TABLE sofia.organizations 
ADD COLUMN IF NOT EXISTS type_id INTEGER REFERENCES sofia.types(id);

UPDATE sofia.organizations o
SET type_id = get_type_id(o.type, 'organization_type')
WHERE type_id IS NULL AND type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_organizations_type_id ON sofia.organizations(type_id);

-- 2. Organizations: industry VARCHAR → industry_id FK
ALTER TABLE sofia.organizations 
ADD COLUMN IF NOT EXISTS industry_id INTEGER REFERENCES sofia.types(id);

UPDATE sofia.organizations o
SET industry_id = get_type_id(o.industry, 'industry')
WHERE industry_id IS NULL AND industry IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_organizations_industry_id ON sofia.organizations(industry_id);

-- 3. Organizations: size VARCHAR → size_id FK
ALTER TABLE sofia.organizations 
ADD COLUMN IF NOT EXISTS size_id INTEGER REFERENCES sofia.types(id);

UPDATE sofia.organizations o
SET size_id = get_type_id(o.size, 'organization_size')
WHERE size_id IS NULL AND size IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_organizations_size_id ON sofia.organizations(size_id);

-- 4. Sources: category VARCHAR → category_id FK
ALTER TABLE sofia.sources 
ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES sofia.types(id);

UPDATE sofia.sources s
SET category_id = get_type_id(s.category, 'source_category')
WHERE category_id IS NULL AND category IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sources_category_id ON sofia.sources(category_id);

-- 5. Sources: data_type VARCHAR → data_type_id FK
ALTER TABLE sofia.sources 
ADD COLUMN IF NOT EXISTS data_type_id INTEGER REFERENCES sofia.types(id);

UPDATE sofia.sources s
SET data_type_id = get_type_id(s.data_type, 'data_type')
WHERE data_type_id IS NULL AND data_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sources_data_type_id ON sofia.sources(data_type_id);

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================

SELECT 
    'types table' AS status,
    COUNT(*) AS total_types,
    COUNT(DISTINCT category) AS categories
FROM sofia.types;

SELECT 
    'types by category' AS report,
    category,
    COUNT(*) AS count
FROM sofia.types
WHERE active = true
GROUP BY category
ORDER BY category;

SELECT 
    'migration status' AS report,
    'organizations.type_id' AS field,
    COUNT(*) AS total,
    COUNT(type_id) AS migrated,
    ROUND(100.0 * COUNT(type_id) / NULLIF(COUNT(*), 0), 2) || '%' AS coverage
FROM sofia.organizations
UNION ALL
SELECT 
    'migration status',
    'sources.category_id',
    COUNT(*),
    COUNT(category_id),
    ROUND(100.0 * COUNT(category_id) / NULLIF(COUNT(*), 0), 2) || '%'
FROM sofia.sources;
