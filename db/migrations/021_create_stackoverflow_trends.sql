CREATE TABLE IF NOT EXISTS sofia.stackoverflow_trends (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(255) NOT NULL,
    count INTEGER,
    is_moderator_only BOOLEAN,
    is_required BOOLEAN,
    has_synonyms BOOLEAN,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start DATE,
    UNIQUE(tag_name, period_start)
);

CREATE INDEX IF NOT EXISTS idx_stackoverflow_tag ON sofia.stackoverflow_trends(tag_name);
CREATE INDEX IF NOT EXISTS idx_stackoverflow_date ON sofia.stackoverflow_trends(collected_at);
