-- ============================================================================
-- ACLED Metadata Migration - Fix Versioning Constraints
-- ============================================================================
-- Purpose: Allow multiple versions of the same dataset to be tracked
-- Issue: UNIQUE(dataset_slug) prevents historical tracking
-- Solution: Change to UNIQUE(dataset_slug, file_hash)
-- ============================================================================

BEGIN;

-- Drop existing unique constraint on dataset_slug
ALTER TABLE acled_metadata.datasets 
    DROP CONSTRAINT IF EXISTS datasets_dataset_slug_key;

-- Add new composite unique constraint for versioning
ALTER TABLE acled_metadata.datasets 
    ADD CONSTRAINT datasets_dataset_slug_hash_unique 
    UNIQUE (dataset_slug, file_hash);

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_datasets_slug_collected 
    ON acled_metadata.datasets(dataset_slug, collected_at DESC);

-- Update the latest_datasets view to handle multiple versions
DROP VIEW IF EXISTS acled_metadata.latest_datasets;

CREATE VIEW acled_metadata.latest_datasets AS
SELECT DISTINCT ON (dataset_slug)
    id,
    dataset_slug,
    source_url,
    download_url,
    aggregation_level,
    region,
    file_hash,
    file_name,
    file_size_bytes,
    collected_at,
    is_aggregated,
    source_type,
    detected_columns,
    version_date,
    created_at,
    updated_at
FROM acled_metadata.datasets
ORDER BY dataset_slug, collected_at DESC;

COMMENT ON VIEW acled_metadata.latest_datasets IS 
'Returns the most recently collected version of each dataset';

-- Add index for is_aggregated to support validation queries
CREATE INDEX IF NOT EXISTS idx_datasets_is_aggregated 
    ON acled_metadata.datasets(is_aggregated);

-- Create a view for version history
CREATE OR REPLACE VIEW acled_metadata.version_history AS
SELECT 
    dataset_slug,
    COUNT(*) as version_count,
    MIN(collected_at) as first_collected,
    MAX(collected_at) as last_collected,
    array_agg(file_hash ORDER BY collected_at) as hash_history
FROM acled_metadata.datasets
GROUP BY dataset_slug;

COMMENT ON VIEW acled_metadata.version_history IS 
'Shows version history for each dataset with hash lineage';

COMMIT;

-- Verification query (run manually after migration)
-- SELECT dataset_slug, COUNT(*), MAX(collected_at) as latest 
-- FROM acled_metadata.datasets 
-- GROUP BY dataset_slug 
-- HAVING COUNT(*) > 1;
