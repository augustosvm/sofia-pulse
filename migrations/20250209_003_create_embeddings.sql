CREATE TABLE IF NOT EXISTS sofia.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, source VARCHAR(100) NOT NULL,
    source_id VARCHAR(200), title TEXT, content TEXT NOT NULL,
    embedding vector(768), metadata JSONB DEFAULT '{}', url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_emb_vec ON sofia.embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);
CREATE INDEX IF NOT EXISTS idx_emb_entity ON sofia.embeddings(entity_type);
