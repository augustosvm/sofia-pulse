-- Migration: Normalize Research Papers Authors
-- Date: 2026-01-20
-- Description: Creates a junction table to link research_papers to persons (authors).
--              This allows strict referential integrity and richer author metadata.

-- Drop table if exists to ensure schema alignment (dev/recovery phase)
DROP TABLE IF EXISTS sofia.paper_authors;

CREATE TABLE IF NOT EXISTS sofia.paper_authors (
    paper_id INTEGER NOT NULL REFERENCES sofia.research_papers(id) ON DELETE CASCADE,
    person_id INTEGER NOT NULL REFERENCES sofia.persons(id) ON DELETE CASCADE,
    author_order INTEGER DEFAULT 0,
    author_name_raw TEXT, -- Nome exato como aparece neste paper
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Composite PK allowing strict ordering management
    PRIMARY KEY (paper_id, person_id, author_order)
);

-- Index for fast lookups by person (Profile View)
CREATE INDEX IF NOT EXISTS idx_paper_authors_person_id ON sofia.paper_authors(person_id);

-- Index for fast lookups by paper (Paper Detail View)
CREATE INDEX IF NOT EXISTS idx_paper_authors_paper_id ON sofia.paper_authors(paper_id);

-- Comments
COMMENT ON TABLE sofia.paper_authors IS 'Junction table linking research papers to their authors (persons)';
COMMENT ON COLUMN sofia.paper_authors.author_name_raw IS 'Original name string as it appeared in the specific paper source';
