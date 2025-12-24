-- Migration 024: Add metadata column to persons table
-- Date: 22 Dez 2025
-- Purpose: Add JSONB metadata column for type-specific fields

BEGIN;

-- Add metadata column if it doesn't exist
ALTER TABLE sofia.persons
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Create index on metadata
CREATE INDEX IF NOT EXISTS idx_persons_metadata ON sofia.persons USING GIN(metadata);

-- Add comment
COMMENT ON COLUMN sofia.persons.metadata IS 'Type-specific fields stored as JSONB';

COMMIT;
