-- ============================================================
-- CRIAR TABELA TYPES - Versão Simplificada
-- ============================================================

-- Criar tabela types
CREATE TABLE IF NOT EXISTS sofia.types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    normalized_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES sofia.types(id),
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_types_normalized_name ON sofia.types(normalized_name);
CREATE INDEX IF NOT EXISTS idx_types_category ON sofia.types(category);
CREATE INDEX IF NOT EXISTS idx_types_parent ON sofia.types(parent_id);
CREATE INDEX IF NOT EXISTS idx_types_active ON sofia.types(active);

-- Popular types básicos
INSERT INTO sofia.types (name, normalized_name, category, description, display_order) VALUES
-- Organization Types
('University', 'university', 'organization_type', 'Universidade', 10),
('Research Center', 'research_center', 'organization_type', 'Centro de Pesquisa', 20),
('Company', 'company', 'organization_type', 'Empresa', 30),
('Startup', 'startup', 'organization_type', 'Startup', 40),
('Government', 'government', 'organization_type', 'Órgão Governamental', 50),
('NGO', 'ngo', 'organization_type', 'ONG', 60),
('Hospital', 'hospital', 'organization_type', 'Hospital', 70),
('School', 'school', 'organization_type', 'Escola', 80),
('Laboratory', 'laboratory', 'organization_type', 'Laboratório', 90),

-- Person Roles
('Researcher', 'researcher', 'person_role', 'Pesquisador', 10),
('Inventor', 'inventor', 'person_role', 'Inventor', 20),
('Developer', 'developer', 'person_role', 'Desenvolvedor', 30),
('Author', 'author', 'person_role', 'Autor', 40),
('CEO', 'ceo', 'person_role', 'CEO', 50),
('Founder', 'founder', 'person_role', 'Fundador', 60),
('CTO', 'cto', 'person_role', 'CTO', 70),
('Engineer', 'engineer', 'person_role', 'Engenheiro', 80),

-- Industries
('Technology', 'technology', 'industry', 'Tecnologia', 10),
('Healthcare', 'healthcare', 'industry', 'Saúde', 20),
('Finance', 'finance', 'industry', 'Finanças', 30),
('Education', 'education', 'industry', 'Educação', 40),
('Energy', 'energy', 'industry', 'Energia', 50)
ON CONFLICT (normalized_name) DO NOTHING;

-- Verificar
SELECT 'types criada' AS status, COUNT(*) AS total FROM sofia.types;
