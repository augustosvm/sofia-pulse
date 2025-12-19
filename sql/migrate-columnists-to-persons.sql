-- ============================================================
-- MIGRAR COLUMNISTS PARA PERSONS
-- ============================================================

-- Adicionar role 'columnist' aos types se não existir
INSERT INTO sofia.types (name, normalized_name, category, description, display_order)
VALUES ('Columnist', 'columnist', 'person_role', 'Colunista', 100)
ON CONFLICT (normalized_name) DO NOTHING;

-- Migrar columnists para persons
INSERT INTO sofia.persons (
    full_name,
    normalized_name,
    bio,
    roles,
    platform,
    source_id,
    metadata,
    created_at
)
SELECT 
    c.name,
    LOWER(TRIM(REGEXP_REPLACE(c.name, '\s+', ' ', 'g'))),
    c.bio,
    ARRAY['columnist'],
    'wordpress',
    (SELECT id FROM sofia.sources WHERE name = 'manual' LIMIT 1),
    jsonb_build_object(
        'wordpress_id', c.wordpress_id,
        'slug', c.slug,
        'migrated_from', 'columnists'
    ),
    c.created_at
FROM sofia.columnists c
WHERE NOT EXISTS (
    SELECT 1 FROM sofia.persons p
    WHERE LOWER(TRIM(REGEXP_REPLACE(p.full_name, '\s+', ' ', 'g'))) = 
          LOWER(TRIM(REGEXP_REPLACE(c.name, '\s+', ' ', 'g')))
);

-- Verificar migração
SELECT 
    'Columnists migrados' AS status,
    COUNT(*) AS total
FROM sofia.persons
WHERE 'columnist' = ANY(roles);

-- Tabela columnists pode ser removida após validação
-- DROP TABLE IF EXISTS sofia.columnists CASCADE;
-- DROP TABLE IF EXISTS sofia.columnist_insights CASCADE;
-- DROP TABLE IF EXISTS sofia.columnist_papers CASCADE;
