-- ============================================================
-- EXPANDIR TABELA PERSONS EXISTENTE
-- Adiciona campos para unificar authors/inventors/etc
-- ============================================================

-- 1. Adicionar novos campos à tabela persons existente
ALTER TABLE sofia.persons 
ADD COLUMN IF NOT EXISTS roles TEXT[],  -- ['author', 'inventor', 'ceo', 'founder', 'researcher']
ADD COLUMN IF NOT EXISTS platform VARCHAR(50),  -- 'hackernews', 'reddit', 'github', 'linkedin', 'openalex'
ADD COLUMN IF NOT EXISTS username VARCHAR(100),
ADD COLUMN IF NOT EXISTS email VARCHAR(300),
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS twitter_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS github_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS website_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES sofia.sources(id),
ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES sofia.companies(id),
ADD COLUMN IF NOT EXISTS h_index INTEGER,
ADD COLUMN IF NOT EXISTS citation_count BIGINT,
ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- 2. Criar índices nos novos campos
CREATE INDEX IF NOT EXISTS idx_persons_roles ON sofia.persons USING GIN(roles);
CREATE INDEX IF NOT EXISTS idx_persons_platform ON sofia.persons(platform);
CREATE INDEX IF NOT EXISTS idx_persons_username ON sofia.persons(username);
CREATE INDEX IF NOT EXISTS idx_persons_source ON sofia.persons(source_id);
CREATE INDEX IF NOT EXISTS idx_persons_company ON sofia.persons(company_id);
CREATE INDEX IF NOT EXISTS idx_persons_active ON sofia.persons(active);

-- 3. Popular roles baseado em dados existentes
-- Pessoas com papers = researchers
UPDATE sofia.persons p
SET roles = ARRAY['researcher']
WHERE EXISTS (
    SELECT 1 FROM sofia.person_papers pp WHERE pp.person_id = p.id
)
AND (roles IS NULL OR 'researcher' != ALL(COALESCE(roles, ARRAY[]::TEXT[])));

-- Pessoas com patents = inventors
UPDATE sofia.persons p
SET roles = array(SELECT DISTINCT unnest(COALESCE(roles, ARRAY[]::TEXT[]) || ARRAY['inventor']))
WHERE EXISTS (
    SELECT 1 FROM sofia.person_patents pp WHERE pp.person_id = p.id
)
AND (roles IS NULL OR 'inventor' != ALL(COALESCE(roles, ARRAY[]::TEXT[])));

-- Pessoas com github repos = developers
UPDATE sofia.persons p
SET roles = array(SELECT DISTINCT unnest(COALESCE(roles, ARRAY[]::TEXT[]) || ARRAY['developer']))
WHERE EXISTS (
    SELECT 1 FROM sofia.person_github_repos pgr WHERE pgr.person_id = p.id
)
AND (roles IS NULL OR 'developer' != ALL(COALESCE(roles, ARRAY[]::TEXT[])));

-- 4. Popular source_id baseado em plataforma/origem
-- OpenAlex (se tiver orcid_id)
UPDATE sofia.persons
SET source_id = get_source_id('openalex'),
    platform = 'openalex'
WHERE orcid_id IS NOT NULL
AND source_id IS NULL;

-- 5. Atualizar função get_or_create_person para usar tabela existente
CREATE OR REPLACE FUNCTION get_or_create_person(
    person_name TEXT,
    person_platform TEXT DEFAULT NULL,
    person_username TEXT DEFAULT NULL,
    person_roles TEXT[] DEFAULT NULL,
    person_source_id INTEGER DEFAULT NULL
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
    
    -- Buscar existente por nome normalizado e plataforma
    SELECT id INTO person_id_result
    FROM sofia.persons
    WHERE normalized_name = normalized
      AND (platform = person_platform OR (platform IS NULL AND person_platform IS NULL))
    LIMIT 1;
    
    IF person_id_result IS NULL THEN
        -- Criar novo
        INSERT INTO sofia.persons (
            full_name, normalized_name, platform, username, roles, source_id
        )
        VALUES (
            TRIM(person_name), normalized, person_platform, person_username, 
            person_roles, person_source_id
        )
        RETURNING id INTO person_id_result;
    ELSE
        -- Atualizar roles se fornecido
        IF person_roles IS NOT NULL THEN
            UPDATE sofia.persons
            SET roles = array(
                SELECT DISTINCT unnest(COALESCE(roles, ARRAY[]::TEXT[]) || person_roles)
            )
            WHERE id = person_id_result;
        END IF;
        
        -- Atualizar source_id se fornecido e ainda NULL
        IF person_source_id IS NOT NULL THEN
            UPDATE sofia.persons
            SET source_id = person_source_id
            WHERE id = person_id_result
            AND source_id IS NULL;
        END IF;
    END IF;
    
    RETURN person_id_result;
END;
$$ LANGUAGE plpgsql;

-- 6. Migrar dados de authors para persons (se necessário)
-- Verificar se há authors que não estão em persons
INSERT INTO sofia.persons (
    full_name, normalized_name, orcid_id, h_index, citation_count,
    roles, source_id, platform, metadata
)
SELECT 
    a.full_name,
    normalize_string(a.full_name),
    a.orcid,
    a.h_index,
    a.citation_count,
    ARRAY['researcher'],
    get_source_id('openalex'),
    'openalex',
    jsonb_build_object(
        'openalex_id', a.openalex_id,
        'detected_gender', a.detected_gender,
        'gender_confidence', a.gender_confidence
    )
FROM sofia.authors a
WHERE NOT EXISTS (
    SELECT 1 FROM sofia.persons p 
    WHERE p.orcid_id = a.orcid 
    OR normalize_string(p.full_name) = normalize_string(a.full_name)
)
ON CONFLICT DO NOTHING;

-- 7. Criar view para compatibilidade com código antigo
CREATE OR REPLACE VIEW sofia.authors_view AS
SELECT 
    id,
    full_name,
    normalized_name,
    orcid_id as orcid,
    h_index,
    citation_count,
    metadata->>'openalex_id' as openalex_id,
    metadata->>'detected_gender' as detected_gender,
    (metadata->>'gender_confidence')::DOUBLE PRECISION as gender_confidence,
    source_id,
    created_at
FROM sofia.persons
WHERE 'researcher' = ANY(COALESCE(roles, ARRAY[]::TEXT[]))
   OR 'author' = ANY(COALESCE(roles, ARRAY[]::TEXT[]));

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================

SELECT 
    'persons table expanded' AS status,
    COUNT(*) AS total_persons,
    COUNT(CASE WHEN 'researcher' = ANY(roles) THEN 1 END) AS researchers,
    COUNT(CASE WHEN 'inventor' = ANY(roles) THEN 1 END) AS inventors,
    COUNT(CASE WHEN 'developer' = ANY(roles) THEN 1 END) AS developers,
    COUNT(CASE WHEN 'author' = ANY(roles) THEN 1 END) AS authors,
    COUNT(source_id) AS with_source,
    COUNT(company_id) AS with_company
FROM sofia.persons;

SELECT 
    'persons by platform' AS report,
    platform,
    COUNT(*) AS count
FROM sofia.persons
WHERE platform IS NOT NULL
GROUP BY platform
ORDER BY count DESC;

SELECT 
    'persons by role' AS report,
    unnest(roles) AS role,
    COUNT(*) AS count
FROM sofia.persons
WHERE roles IS NOT NULL
GROUP BY role
ORDER BY count DESC;
