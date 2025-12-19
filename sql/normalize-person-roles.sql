-- ============================================================
-- NORMALIZAR ROLES - Tabela de Relacionamento
-- Remove TEXT[] roles e cria person_roles com FK
-- ============================================================

-- 1. Criar tabela de relacionamento person_roles
CREATE TABLE IF NOT EXISTS sofia.person_roles (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL REFERENCES sofia.persons(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES sofia.types(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,
    started_at DATE,
    ended_at DATE,
    organization_id INTEGER REFERENCES sofia.organizations(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(person_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_person_roles_person ON sofia.person_roles(person_id);
CREATE INDEX IF NOT EXISTS idx_person_roles_role ON sofia.person_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_person_roles_org ON sofia.person_roles(organization_id);
CREATE INDEX IF NOT EXISTS idx_person_roles_primary ON sofia.person_roles(is_primary);

-- 2. Migrar dados de persons.roles (TEXT[]) para person_roles
INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
SELECT 
    p.id,
    t.id,
    true  -- primeiro role é primary
FROM sofia.persons p
CROSS JOIN LATERAL unnest(p.roles) AS role_name
JOIN sofia.types t ON t.normalized_name = LOWER(role_name) AND t.category = 'person_role'
WHERE p.roles IS NOT NULL
ON CONFLICT (person_id, role_id) DO NOTHING;

-- 3. Criar view para compatibilidade
CREATE OR REPLACE VIEW sofia.persons_with_roles AS
SELECT 
    p.*,
    array_agg(DISTINCT t.name ORDER BY t.name) FILTER (WHERE t.name IS NOT NULL) AS role_names,
    array_agg(DISTINCT t.id ORDER BY t.id) FILTER (WHERE t.id IS NOT NULL) AS role_ids
FROM sofia.persons p
LEFT JOIN sofia.person_roles pr ON p.id = pr.person_id
LEFT JOIN sofia.types t ON pr.role_id = t.id
GROUP BY p.id;

-- 4. Função helper para adicionar role
CREATE OR REPLACE FUNCTION add_person_role(
    p_person_id INTEGER,
    p_role_name TEXT,
    p_is_primary BOOLEAN DEFAULT false,
    p_organization_id INTEGER DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    role_id_result INTEGER;
    person_role_id INTEGER;
BEGIN
    -- Buscar role_id
    SELECT id INTO role_id_result
    FROM sofia.types
    WHERE normalized_name = LOWER(TRIM(p_role_name))
    AND category = 'person_role'
    LIMIT 1;
    
    IF role_id_result IS NULL THEN
        RAISE EXCEPTION 'Role % não encontrado', p_role_name;
    END IF;
    
    -- Inserir person_role
    INSERT INTO sofia.person_roles (person_id, role_id, is_primary, organization_id)
    VALUES (p_person_id, role_id_result, p_is_primary, p_organization_id)
    ON CONFLICT (person_id, role_id) DO UPDATE
    SET is_primary = EXCLUDED.is_primary,
        organization_id = COALESCE(EXCLUDED.organization_id, person_roles.organization_id)
    RETURNING id INTO person_role_id;
    
    RETURN person_role_id;
END;
$$ LANGUAGE plpgsql;

-- 5. Verificação
SELECT 
    'person_roles criada' AS status,
    COUNT(*) AS total_roles,
    COUNT(DISTINCT person_id) AS unique_persons
FROM sofia.person_roles;

SELECT 
    'Roles por pessoa' AS report,
    t.name AS role,
    COUNT(*) AS count
FROM sofia.person_roles pr
JOIN sofia.types t ON pr.role_id = t.id
GROUP BY t.name
ORDER BY count DESC;

-- 6. Após validação, remover coluna roles antiga
-- ALTER TABLE sofia.persons DROP COLUMN IF EXISTS roles;
