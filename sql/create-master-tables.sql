-- ============================================================
-- NORMALIZAÇÃO COMPLETA - Master Tables
-- Cria todas as tabelas master para entidades repetidas
-- ============================================================

-- 1. TRENDS (tecnologias, frameworks, linguagens)
CREATE TABLE IF NOT EXISTS sofia.trends (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    normalized_name VARCHAR(200) UNIQUE NOT NULL,  -- lowercase, sem espaços
    category VARCHAR(100),  -- 'language', 'framework', 'library', 'tool', 'platform'
    aliases TEXT[],  -- variações do nome
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trends_normalized_name ON sofia.trends(normalized_name);
CREATE INDEX IF NOT EXISTS idx_trends_category ON sofia.trends(category);

-- 2. COMPANIES (empresas, startups, organizações)
CREATE TABLE IF NOT EXISTS sofia.companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) UNIQUE NOT NULL,
    normalized_name VARCHAR(300) UNIQUE NOT NULL,
    aliases TEXT[],
    industry VARCHAR(100),
    country_id INTEGER REFERENCES sofia.countries(id),
    website VARCHAR(500),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_normalized_name ON sofia.companies(normalized_name);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON sofia.companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_country ON sofia.companies(country_id);

-- 3. PERSONS (pessoas: autores, inventores, CEOs, fundadores)
CREATE TABLE IF NOT EXISTS sofia.persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    email VARCHAR(300),
    username VARCHAR(100),
    platform VARCHAR(50),  -- 'hackernews', 'reddit', 'github', 'linkedin', 'academic'
    roles TEXT[],  -- ['author', 'inventor', 'ceo', 'founder', 'researcher']
    company_id INTEGER REFERENCES sofia.companies(id),
    country_id INTEGER REFERENCES sofia.countries(id),
    bio TEXT,
    profile_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    twitter_url VARCHAR(500),
    github_url VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(normalized_name, platform)
);

CREATE INDEX IF NOT EXISTS idx_persons_normalized_name ON sofia.persons(normalized_name);
CREATE INDEX IF NOT EXISTS idx_persons_platform ON sofia.persons(platform);
CREATE INDEX IF NOT EXISTS idx_persons_username ON sofia.persons(username);
CREATE INDEX IF NOT EXISTS idx_persons_roles ON sofia.persons USING GIN(roles);
CREATE INDEX IF NOT EXISTS idx_persons_company ON sofia.persons(company_id);
CREATE INDEX IF NOT EXISTS idx_persons_country ON sofia.persons(country_id);

-- 4. CATEGORIES (categorias genéricas reutilizáveis)
CREATE TABLE IF NOT EXISTS sofia.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    normalized_name VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES sofia.categories(id),
    type VARCHAR(50),  -- 'tech', 'industry', 'topic', 'skill'
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_categories_normalized_name ON sofia.categories(normalized_name);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON sofia.categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_type ON sofia.categories(type);

-- ============================================================
-- FUNÇÕES HELPER PARA NORMALIZAÇÃO
-- ============================================================

-- Normalizar string (lowercase, trim, remove espaços extras)
CREATE OR REPLACE FUNCTION normalize_string(input TEXT)
RETURNS TEXT AS $$
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN NULL;
    END IF;
    
    RETURN LOWER(TRIM(REGEXP_REPLACE(input, '\s+', ' ', 'g')));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get or create trend
CREATE OR REPLACE FUNCTION get_or_create_trend(
    trend_name TEXT,
    trend_category TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    trend_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF trend_name IS NULL OR TRIM(trend_name) = '' THEN
        RETURN NULL;
    END IF;
    
    normalized := normalize_string(trend_name);
    
    -- Buscar existente
    SELECT id INTO trend_id_result
    FROM sofia.trends
    WHERE normalized_name = normalized
    LIMIT 1;
    
    -- Se não encontrou, criar
    IF trend_id_result IS NULL THEN
        INSERT INTO sofia.trends (name, normalized_name, category)
        VALUES (TRIM(trend_name), normalized, trend_category)
        ON CONFLICT (normalized_name) DO NOTHING
        RETURNING id INTO trend_id_result;
        
        -- Se ainda NULL (conflito), buscar novamente
        IF trend_id_result IS NULL THEN
            SELECT id INTO trend_id_result
            FROM sofia.trends
            WHERE normalized_name = normalized
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN trend_id_result;
END;
$$ LANGUAGE plpgsql;

-- Get or create company
CREATE OR REPLACE FUNCTION get_or_create_company(
    company_name TEXT,
    company_industry TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    company_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF company_name IS NULL OR TRIM(company_name) = '' THEN
        RETURN NULL;
    END IF;
    
    normalized := normalize_string(company_name);
    
    SELECT id INTO company_id_result
    FROM sofia.companies
    WHERE normalized_name = normalized
    LIMIT 1;
    
    IF company_id_result IS NULL THEN
        INSERT INTO sofia.companies (name, normalized_name, industry)
        VALUES (TRIM(company_name), normalized, company_industry)
        ON CONFLICT (normalized_name) DO NOTHING
        RETURNING id INTO company_id_result;
        
        IF company_id_result IS NULL THEN
            SELECT id INTO company_id_result
            FROM sofia.companies
            WHERE normalized_name = normalized
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN company_id_result;
END;
$$ LANGUAGE plpgsql;

-- Get or create person
CREATE OR REPLACE FUNCTION get_or_create_person(
    person_name TEXT,
    person_platform TEXT DEFAULT NULL,
    person_username TEXT DEFAULT NULL,
    person_roles TEXT[] DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    person_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF person_name IS NULL OR TRIM(person_name) = '' THEN
        RETURN NULL;
    END IF;
    
    normalized := normalize_string(person_name);
    
    SELECT id INTO person_id_result
    FROM sofia.persons
    WHERE normalized_name = normalized
      AND (platform = person_platform OR (platform IS NULL AND person_platform IS NULL))
    LIMIT 1;
    
    IF person_id_result IS NULL THEN
        INSERT INTO sofia.persons (name, normalized_name, platform, username, roles)
        VALUES (TRIM(person_name), normalized, person_platform, person_username, person_roles)
        ON CONFLICT (normalized_name, platform) DO NOTHING
        RETURNING id INTO person_id_result;
        
        IF person_id_result IS NULL THEN
            SELECT id INTO person_id_result
            FROM sofia.persons
            WHERE normalized_name = normalized
              AND (platform = person_platform OR (platform IS NULL AND person_platform IS NULL))
            LIMIT 1;
        END IF;
    ELSE
        -- Atualizar roles se fornecido
        IF person_roles IS NOT NULL THEN
            UPDATE sofia.persons
            SET roles = array(SELECT DISTINCT unnest(COALESCE(roles, ARRAY[]::TEXT[]) || person_roles))
            WHERE id = person_id_result;
        END IF;
    END IF;
    
    RETURN person_id_result;
END;
$$ LANGUAGE plpgsql;

-- Get or create category
CREATE OR REPLACE FUNCTION get_or_create_category(
    category_name TEXT,
    category_type TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    category_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF category_name IS NULL OR TRIM(category_name) = '' THEN
        RETURN NULL;
    END IF;
    
    normalized := normalize_string(category_name);
    
    SELECT id INTO category_id_result
    FROM sofia.categories
    WHERE normalized_name = normalized
    LIMIT 1;
    
    IF category_id_result IS NULL THEN
        INSERT INTO sofia.categories (name, normalized_name, type)
        VALUES (TRIM(category_name), normalized, category_type)
        ON CONFLICT (normalized_name) DO NOTHING
        RETURNING id INTO category_id_result;
        
        IF category_id_result IS NULL THEN
            SELECT id INTO category_id_result
            FROM sofia.categories
            WHERE normalized_name = normalized
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN category_id_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================

SELECT 'Master Tables Created' AS status;

SELECT 
    'trends' AS table_name,
    COUNT(*) AS records
FROM sofia.trends
UNION ALL
SELECT 'companies', COUNT(*) FROM sofia.companies
UNION ALL
SELECT 'persons', COUNT(*) FROM sofia.persons
UNION ALL
SELECT 'categories', COUNT(*) FROM sofia.categories;
