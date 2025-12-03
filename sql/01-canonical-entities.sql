-- ============================================================================
-- CANONICAL ENTITIES - Universal Entity Resolution System
-- ============================================================================
-- Purpose: Enable cross-source entity linking for:
--   - GitHub repos ↔ ArXiv papers
--   - Companies ↔ Funding rounds ↔ GitHub ↔ Patents
--   - Researchers ↔ Papers ↔ Affiliations
--   - Technologies ↔ Patents ↔ Repos ↔ Research
-- ============================================================================

-- Create entity types enum
CREATE TYPE sofia.entity_type AS ENUM (
    'company',           -- Startup, corporation, NGO
    'person',            -- Founder, researcher, athlete, politician
    'technology',        -- AI model, framework, protocol
    'paper',             -- Academic paper, preprint
    'repository',        -- GitHub repo, GitLab project
    'patent',            -- Patent application/grant
    'product',           -- Software product, hardware
    'organization',      -- University, research lab, foundation
    'location',          -- City, country, region
    'event',             -- Conference, tournament, crisis
    'indicator',         -- Economic indicator, metric
    'project'            -- Research project, initiative
);

-- Main canonical entities table
CREATE TABLE IF NOT EXISTS sofia.canonical_entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type sofia.entity_type NOT NULL,

    -- Primary identification
    canonical_name TEXT NOT NULL,           -- Normalized, deduplicated name
    normalized_name TEXT NOT NULL,          -- Lowercase, no special chars (for fuzzy matching)

    -- Semantic search
    name_embedding vector(384),             -- Mastra embedding for semantic matching
    description TEXT,                       -- Entity description
    description_embedding vector(384),      -- Description embedding

    -- Metadata
    aliases TEXT[] DEFAULT '{}',            -- Alternative names, abbreviations
    metadata JSONB DEFAULT '{}',            -- Flexible metadata (website, logo, etc.)
    confidence_score FLOAT DEFAULT 1.0,     -- Entity resolution confidence (0-1)

    -- Provenance
    primary_source TEXT,                    -- Main source of truth (e.g., 'github', 'arxiv')
    source_count INTEGER DEFAULT 1,         -- How many sources mention this entity

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),   -- Last time entity appeared in any source

    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Create indexes
CREATE INDEX idx_canonical_entities_type ON sofia.canonical_entities(entity_type);
CREATE INDEX idx_canonical_entities_normalized ON sofia.canonical_entities(normalized_name);
CREATE INDEX idx_canonical_entities_primary_source ON sofia.canonical_entities(primary_source);
CREATE INDEX idx_canonical_entities_last_seen ON sofia.canonical_entities(last_seen_at DESC);

-- GIN index for aliases array search
CREATE INDEX idx_canonical_entities_aliases ON sofia.canonical_entities USING GIN(aliases);

-- HNSW indexes for vector similarity search
CREATE INDEX idx_canonical_entities_name_vec ON sofia.canonical_entities
    USING hnsw (name_embedding vector_l2_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_canonical_entities_desc_vec ON sofia.canonical_entities
    USING hnsw (description_embedding vector_l2_ops)
    WITH (m = 16, ef_construction = 64);

COMMENT ON TABLE sofia.canonical_entities IS 'Universal entity resolution table - maps entities across all data sources';
COMMENT ON COLUMN sofia.canonical_entities.entity_id IS 'UUID - universal identifier across all Sofia sources';
COMMENT ON COLUMN sofia.canonical_entities.normalized_name IS 'Lowercase, ASCII-only version for fuzzy matching';
COMMENT ON COLUMN sofia.canonical_entities.confidence_score IS 'Entity resolution confidence: 1.0 = exact match, 0.7-0.9 = fuzzy match, <0.7 = low confidence';

-- ============================================================================
-- ENTITY MAPPINGS - Links source-specific IDs to canonical entities
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.entity_mappings (
    id SERIAL PRIMARY KEY,
    entity_id UUID NOT NULL REFERENCES sofia.canonical_entities(entity_id) ON DELETE CASCADE,

    -- Source identification
    source_name TEXT NOT NULL,              -- e.g., 'github', 'arxiv', 'world_bank', 'hacker_news'
    source_table TEXT NOT NULL,             -- Table name in sofia schema
    source_id TEXT NOT NULL,                -- ID in source system (repo_id, paper_id, etc.)
    source_pk INTEGER,                      -- Primary key in source table (optional)

    -- Matching metadata
    match_method TEXT NOT NULL,             -- 'exact', 'fuzzy', 'embedding', 'manual'
    match_confidence FLOAT DEFAULT 1.0,     -- Confidence in this mapping (0-1)

    -- Raw source data
    source_name_raw TEXT,                   -- Original name in source
    source_data JSONB DEFAULT '{}',         -- Full source record (for debugging)

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(source_name, source_table, source_id),
    CONSTRAINT valid_match_confidence CHECK (match_confidence >= 0 AND match_confidence <= 1)
);

CREATE INDEX idx_entity_mappings_entity_id ON sofia.entity_mappings(entity_id);
CREATE INDEX idx_entity_mappings_source ON sofia.entity_mappings(source_name, source_table);
CREATE INDEX idx_entity_mappings_source_id ON sofia.entity_mappings(source_id);
CREATE INDEX idx_entity_mappings_confidence ON sofia.entity_mappings(match_confidence DESC);

COMMENT ON TABLE sofia.entity_mappings IS 'Maps source-specific IDs to canonical entities - enables cross-source queries';
COMMENT ON COLUMN sofia.entity_mappings.match_method IS 'exact: identical match, fuzzy: Levenshtein/trigram, embedding: vector similarity, manual: human-verified';

-- ============================================================================
-- ENTITY RELATIONSHIPS - Graph of entity connections
-- ============================================================================

CREATE TABLE IF NOT EXISTS sofia.entity_relationships (
    id SERIAL PRIMARY KEY,

    -- Entities
    entity_id_from UUID NOT NULL REFERENCES sofia.canonical_entities(entity_id) ON DELETE CASCADE,
    entity_id_to UUID NOT NULL REFERENCES sofia.canonical_entities(entity_id) ON DELETE CASCADE,

    -- Relationship
    relationship_type TEXT NOT NULL,        -- 'founded_by', 'works_at', 'authored', 'funded', 'cited', 'forked'
    strength FLOAT DEFAULT 1.0,             -- Relationship strength (0-1)

    -- Metadata
    metadata JSONB DEFAULT '{}',            -- Flexible metadata (date, amount, etc.)

    -- Provenance
    source_name TEXT NOT NULL,              -- Where this relationship was discovered
    evidence_count INTEGER DEFAULT 1,       -- How many sources confirm this relationship

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT no_self_reference CHECK (entity_id_from != entity_id_to),
    CONSTRAINT valid_strength CHECK (strength >= 0 AND strength <= 1),
    UNIQUE(entity_id_from, entity_id_to, relationship_type)
);

CREATE INDEX idx_entity_relationships_from ON sofia.entity_relationships(entity_id_from);
CREATE INDEX idx_entity_relationships_to ON sofia.entity_relationships(entity_id_to);
CREATE INDEX idx_entity_relationships_type ON sofia.entity_relationships(relationship_type);
CREATE INDEX idx_entity_relationships_strength ON sofia.entity_relationships(strength DESC);

COMMENT ON TABLE sofia.entity_relationships IS 'Graph of relationships between canonical entities - enables Founder Graph, Innovation Map';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to normalize entity names for fuzzy matching
CREATE OR REPLACE FUNCTION sofia.normalize_entity_name(name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(name, '[^a-zA-Z0-9\s]', '', 'g'),  -- Remove special chars
                '\s+', ' ', 'g'                                    -- Normalize whitespace
            ),
            '^\s+|\s+$', '', 'g'                                  -- Trim
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION sofia.normalize_entity_name IS 'Normalize entity name for fuzzy matching: lowercase, remove special chars, normalize spaces';

-- Function to find or create canonical entity
CREATE OR REPLACE FUNCTION sofia.find_or_create_entity(
    p_name TEXT,
    p_entity_type sofia.entity_type,
    p_source TEXT,
    p_description TEXT DEFAULT NULL,
    p_aliases TEXT[] DEFAULT '{}',
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_entity_id UUID;
    v_normalized TEXT;
BEGIN
    v_normalized := sofia.normalize_entity_name(p_name);

    -- Try exact match first
    SELECT entity_id INTO v_entity_id
    FROM sofia.canonical_entities
    WHERE entity_type = p_entity_type
      AND normalized_name = v_normalized
    LIMIT 1;

    -- If not found, create new entity
    IF v_entity_id IS NULL THEN
        INSERT INTO sofia.canonical_entities (
            entity_type,
            canonical_name,
            normalized_name,
            description,
            aliases,
            metadata,
            primary_source,
            source_count
        ) VALUES (
            p_entity_type,
            p_name,
            v_normalized,
            p_description,
            p_aliases,
            p_metadata,
            p_source,
            1
        )
        RETURNING entity_id INTO v_entity_id;
    ELSE
        -- Update last_seen_at and increment source_count if new source
        UPDATE sofia.canonical_entities
        SET last_seen_at = NOW(),
            updated_at = NOW(),
            source_count = CASE
                WHEN primary_source != p_source THEN source_count + 1
                ELSE source_count
            END
        WHERE entity_id = v_entity_id;
    END IF;

    RETURN v_entity_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.find_or_create_entity IS 'Find existing canonical entity or create new one - handles deduplication';

-- Function to link source record to canonical entity
CREATE OR REPLACE FUNCTION sofia.link_entity_to_source(
    p_entity_id UUID,
    p_source_name TEXT,
    p_source_table TEXT,
    p_source_id TEXT,
    p_source_pk INTEGER DEFAULT NULL,
    p_match_method TEXT DEFAULT 'exact',
    p_match_confidence FLOAT DEFAULT 1.0,
    p_source_name_raw TEXT DEFAULT NULL,
    p_source_data JSONB DEFAULT '{}'
)
RETURNS INTEGER AS $$
DECLARE
    v_mapping_id INTEGER;
BEGIN
    INSERT INTO sofia.entity_mappings (
        entity_id,
        source_name,
        source_table,
        source_id,
        source_pk,
        match_method,
        match_confidence,
        source_name_raw,
        source_data
    ) VALUES (
        p_entity_id,
        p_source_name,
        p_source_table,
        p_source_id,
        p_source_pk,
        p_match_method,
        p_match_confidence,
        p_source_name_raw,
        p_source_data
    )
    ON CONFLICT (source_name, source_table, source_id)
    DO UPDATE SET
        entity_id = EXCLUDED.entity_id,
        match_confidence = EXCLUDED.match_confidence,
        updated_at = NOW()
    RETURNING id INTO v_mapping_id;

    RETURN v_mapping_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.link_entity_to_source IS 'Create or update mapping between source record and canonical entity';

-- Function to find similar entities by embedding
CREATE OR REPLACE FUNCTION sofia.find_similar_entities(
    p_embedding vector(384),
    p_entity_type sofia.entity_type DEFAULT NULL,
    p_limit INTEGER DEFAULT 10,
    p_min_similarity FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    entity_id UUID,
    entity_type sofia.entity_type,
    canonical_name TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ce.entity_id,
        ce.entity_type,
        ce.canonical_name,
        1 - (ce.name_embedding <-> p_embedding) AS similarity
    FROM sofia.canonical_entities ce
    WHERE ce.name_embedding IS NOT NULL
      AND (p_entity_type IS NULL OR ce.entity_type = p_entity_type)
      AND (1 - (ce.name_embedding <-> p_embedding)) >= p_min_similarity
    ORDER BY ce.name_embedding <-> p_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.find_similar_entities IS 'Find canonical entities similar to given embedding - returns entities with similarity >= threshold';

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- View: Entity stats by type
CREATE OR REPLACE VIEW sofia.entity_stats_by_type AS
SELECT
    entity_type,
    COUNT(*) as total_entities,
    AVG(source_count) as avg_sources_per_entity,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) FILTER (WHERE name_embedding IS NOT NULL) as entities_with_embeddings,
    MIN(created_at) as first_created,
    MAX(last_seen_at) as last_seen
FROM sofia.canonical_entities
GROUP BY entity_type
ORDER BY total_entities DESC;

-- View: Cross-source entity coverage
CREATE OR REPLACE VIEW sofia.cross_source_coverage AS
SELECT
    em.source_name,
    ce.entity_type,
    COUNT(DISTINCT em.entity_id) as entities_mapped,
    AVG(em.match_confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE em.match_method = 'exact') as exact_matches,
    COUNT(*) FILTER (WHERE em.match_method = 'fuzzy') as fuzzy_matches,
    COUNT(*) FILTER (WHERE em.match_method = 'embedding') as embedding_matches
FROM sofia.entity_mappings em
JOIN sofia.canonical_entities ce ON em.entity_id = ce.entity_id
GROUP BY em.source_name, ce.entity_type
ORDER BY em.source_name, entities_mapped DESC;

-- View: Relationship network summary
CREATE OR REPLACE VIEW sofia.relationship_network_summary AS
SELECT
    relationship_type,
    COUNT(*) as total_relationships,
    AVG(strength) as avg_strength,
    COUNT(DISTINCT entity_id_from) as unique_sources,
    COUNT(DISTINCT entity_id_to) as unique_targets,
    AVG(evidence_count) as avg_evidence_count
FROM sofia.entity_relationships
GROUP BY relationship_type
ORDER BY total_relationships DESC;

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT ON sofia.canonical_entities TO PUBLIC;
GRANT SELECT ON sofia.entity_mappings TO PUBLIC;
GRANT SELECT ON sofia.entity_relationships TO PUBLIC;
GRANT SELECT ON sofia.entity_stats_by_type TO PUBLIC;
GRANT SELECT ON sofia.cross_source_coverage TO PUBLIC;
GRANT SELECT ON sofia.relationship_network_summary TO PUBLIC;

-- ============================================================================
-- COMPLETE
-- ============================================================================

SELECT 'Canonical Entities system created successfully!' as status;
