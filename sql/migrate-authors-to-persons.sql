-- ============================================================
-- CORREÇÃO: authors → persons (mais genérico)
-- Person pode ser: author, inventor, CEO, founder, researcher
-- ============================================================

-- 1. Renomear tabela authors para persons
ALTER TABLE IF EXISTS sofia.authors RENAME TO persons;

-- 2. Adicionar campos para diferentes roles
ALTER TABLE sofia.persons 
ADD COLUMN IF NOT EXISTS roles TEXT[],  -- ['author', 'inventor', 'ceo', 'founder']
ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES sofia.companies(id),
ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS twitter_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS github_url VARCHAR(500);

-- 3. Atualizar índices
DROP INDEX IF EXISTS idx_authors_normalized_name;
DROP INDEX IF EXISTS idx_authors_platform;
DROP INDEX IF EXISTS idx_authors_username;

CREATE INDEX IF NOT EXISTS idx_persons_normalized_name ON sofia.persons(normalized_name);
CREATE INDEX IF NOT EXISTS idx_persons_platform ON sofia.persons(platform);
CREATE INDEX IF NOT EXISTS idx_persons_username ON sofia.persons(username);
CREATE INDEX IF NOT EXISTS idx_persons_roles ON sofia.persons USING GIN(roles);
CREATE INDEX IF NOT EXISTS idx_persons_company ON sofia.persons(company_id);
CREATE INDEX IF NOT EXISTS idx_persons_country ON sofia.persons(country_id);

-- 4. Atualizar foreign keys em outras tabelas
ALTER TABLE sofia.community_posts 
RENAME COLUMN author_id TO person_id;

-- Se patents tiver inventor_id
ALTER TABLE sofia.patents 
ADD COLUMN IF NOT EXISTS inventor_id INTEGER REFERENCES sofia.persons(id);

-- 5. Atualizar função helper
DROP FUNCTION IF EXISTS get_or_create_author(TEXT, TEXT, TEXT);

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
    
    -- Buscar existente
    SELECT id INTO person_id_result
    FROM sofia.persons
    WHERE normalized_name = normalized
      AND (platform = person_platform OR (platform IS NULL AND person_platform IS NULL))
    LIMIT 1;
    
    -- Se não encontrou, criar
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

-- 6. Popular roles baseado em dados existentes
UPDATE sofia.persons
SET roles = ARRAY['author']
WHERE platform IN ('hackernews', 'reddit', 'devto')
AND (roles IS NULL OR 'author' != ALL(roles));

-- 7. Verificação
SELECT 
    'persons table' AS status,
    COUNT(*) AS total_persons,
    COUNT(DISTINCT normalized_name) AS unique_names,
    COUNT(CASE WHEN 'author' = ANY(roles) THEN 1 END) AS authors,
    COUNT(CASE WHEN 'inventor' = ANY(roles) THEN 1 END) AS inventors,
    COUNT(company_id) AS with_company
FROM sofia.persons;
