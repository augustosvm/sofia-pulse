-- Migration: Normalize Research Papers Authors
-- Date: 2026-01-20
-- Description: Creates a junction table to link research_papers to persons (authors).
--              This allows strict referential integrity and richer author metadata.

-- Removed DROP TABLE as requested (Surgical Fix)
-- Ensure table exists
CREATE TABLE IF NOT EXISTS sofia.paper_authors (
    paper_id INTEGER NOT NULL REFERENCES sofia.research_papers(id) ON DELETE CASCADE,
    person_id INTEGER NOT NULL REFERENCES sofia.persons(id) ON DELETE CASCADE,
    author_order INTEGER DEFAULT 0,
    author_name_raw TEXT, -- Nome exato como aparece neste paper
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraint 1: Strict ordering per paper
    -- Handles duplicates by forcing uniqueness on (paper, order)
    CONSTRAINT unique_paper_author_order UNIQUE (paper_id, author_order),

    -- Constraint 2: One person per paper (usually desired, unless author listed twice?)
    -- Assuming one person shouldn't be listed twice on same paper for normalization
    CONSTRAINT unique_paper_person UNIQUE (paper_id, person_id)
);

-- Index for fast lookups by person (Profile View)
CREATE INDEX IF NOT EXISTS idx_paper_authors_person_id ON sofia.paper_authors(person_id);

-- Index for fast lookups by paper (Paper Detail View)
CREATE INDEX IF NOT EXISTS idx_paper_authors_paper_id ON sofia.paper_authors(paper_id);

-- Comments
COMMENT ON TABLE sofia.paper_authors IS 'Junction table linking research papers to their authors (persons)';
COMMENT ON COLUMN sofia.paper_authors.author_name_raw IS 'Original name string as it appeared in the specific paper source';
