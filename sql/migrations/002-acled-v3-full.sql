-- ============================================================================
-- ACLED v3 Full Schema - Production Ready
-- ============================================================================
-- Purpose: Complete schema for ACLED aggregated data with versioning,
--          failure tracking, and flexible storage
-- ============================================================================

BEGIN;

-- ============================================================================
-- Create Schemas
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS acled_metadata;
CREATE SCHEMA IF NOT EXISTS acled_aggregated;

-- ============================================================================
-- Metadata Table (Extended v3)
-- ============================================================================

CREATE TABLE IF NOT EXISTS acled_metadata.datasets (
    id SERIAL PRIMARY KEY,
    dataset_slug VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    download_url TEXT,
    download_url_final TEXT,  -- After redirects
    aggregation_level VARCHAR(100),
    region VARCHAR(100),
    file_hash VARCHAR(64),  -- SHA256 (nullable for failed attempts)
    file_name VARCHAR(500),
    file_size_bytes BIGINT,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_aggregated BOOLEAN,
    source_type VARCHAR(100),
    detected_columns JSONB,
    version_date DATE,
    
    -- v3 Extensions: Failure tracking
    status VARCHAR(50) NOT NULL DEFAULT 'success',  -- success|failed|invalid
    error_message TEXT,
    http_status INTEGER,
    strategy_used VARCHAR(50),  -- A|B|C|D
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Allow multiple versions AND failed attempts
    CONSTRAINT datasets_slug_hash_unique UNIQUE (dataset_slug, file_hash, collected_at)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_datasets_slug ON acled_metadata.datasets(dataset_slug);
CREATE INDEX IF NOT EXISTS idx_datasets_hash ON acled_metadata.datasets(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_datasets_collected ON acled_metadata.datasets(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON acled_metadata.datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_slug_collected ON acled_metadata.datasets(dataset_slug, collected_at DESC);

-- ============================================================================
-- Aggregated Data Tables (Flexible v3)
-- ============================================================================

-- Country-Year Aggregates
CREATE TABLE IF NOT EXISTS acled_aggregated.country_year (
    id SERIAL PRIMARY KEY,
    dataset_slug VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    events INT,
    fatalities INT,
    civilian_fatalities INT,
    demonstrations INT,
    civilian_targeting_events INT,
    metadata JSONB,  -- All extra columns go here
    source_file_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(dataset_slug, country, year, source_file_hash)
);

CREATE INDEX idx_country_year_country ON acled_aggregated.country_year(country);
CREATE INDEX idx_country_year_year ON acled_aggregated.country_year(year);
CREATE INDEX idx_country_year_slug ON acled_aggregated.country_year(dataset_slug);

-- Country-Month-Year Aggregates
CREATE TABLE IF NOT EXISTS acled_aggregated.country_month_year (
    id SERIAL PRIMARY KEY,
    dataset_slug VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    events INT,
    fatalities INT,
    metadata JSONB,
    source_file_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(dataset_slug, country, year, month, source_file_hash)
);

CREATE INDEX idx_country_month_country ON acled_aggregated.country_month_year(country);
CREATE INDEX idx_country_month_year ON acled_aggregated.country_month_year(year, month);
CREATE INDEX idx_country_month_slug ON acled_aggregated.country_month_year(dataset_slug);

-- Regional Aggregates (Flexible)
CREATE TABLE IF NOT EXISTS acled_aggregated.regional (
    id SERIAL PRIMARY KEY,
    dataset_slug VARCHAR(255) NOT NULL,
    region VARCHAR(100),
    country VARCHAR(255),
    admin1 VARCHAR(255),
    admin2 VARCHAR(255),
    year INT,
    month INT,
    week INT,
    date_range_start DATE,
    date_range_end DATE,
    centroid_latitude DECIMAL(10, 7),
    centroid_longitude DECIMAL(10, 7),
    events INT,
    fatalities INT,
    event_type VARCHAR(100),
    disorder_type VARCHAR(100),
    metadata JSONB,  -- Flexible storage
    source_file_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(dataset_slug, region, country, admin1, admin2, year, month, week, event_type, disorder_type, source_file_hash)
);

CREATE INDEX idx_regional_region ON acled_aggregated.regional(region);
CREATE INDEX idx_regional_country ON acled_aggregated.regional(country);
CREATE INDEX idx_regional_admin1 ON acled_aggregated.regional(admin1);
CREATE INDEX idx_regional_year ON acled_aggregated.regional(year);
CREATE INDEX idx_regional_slug ON acled_aggregated.regional(dataset_slug);

-- ============================================================================
-- Views
-- ============================================================================

-- Latest successful version of each dataset
CREATE OR REPLACE VIEW acled_metadata.latest_datasets AS
SELECT DISTINCT ON (dataset_slug)
    *
FROM acled_metadata.datasets
WHERE status = 'success'
ORDER BY dataset_slug, collected_at DESC;

-- Version history
CREATE OR REPLACE VIEW acled_metadata.version_history AS
SELECT 
    dataset_slug,
    COUNT(*) FILTER (WHERE status = 'success') as successful_versions,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_attempts,
    COUNT(*) FILTER (WHERE status = 'invalid') as invalid_attempts,
    MIN(collected_at) as first_attempt,
    MAX(collected_at) as last_attempt,
    array_agg(file_hash ORDER BY collected_at) FILTER (WHERE file_hash IS NOT NULL) as hash_history
FROM acled_metadata.datasets
GROUP BY dataset_slug;

-- Collection summary
CREATE OR REPLACE VIEW acled_metadata.collection_summary AS
SELECT 
    DATE(collected_at) as collection_date,
    status,
    COUNT(*) as count,
    array_agg(DISTINCT dataset_slug) as datasets
FROM acled_metadata.datasets
GROUP BY DATE(collected_at), status
ORDER BY collection_date DESC, status;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON SCHEMA acled_aggregated IS 'Official ACLED aggregated datasets - NOT derived from events';
COMMENT ON SCHEMA acled_metadata IS 'Metadata and failure tracking for ACLED aggregate collection';

COMMENT ON TABLE acled_metadata.datasets IS 'Tracks all collection attempts (success, failed, invalid) with full audit trail';
COMMENT ON COLUMN acled_metadata.datasets.status IS 'success: data inserted | failed: scraping/download error | invalid: not an official aggregate';
COMMENT ON COLUMN acled_metadata.datasets.strategy_used IS 'A: direct links | B: download buttons | C: content-type | D: wordpress pattern';

COMMENT ON TABLE acled_aggregated.country_year IS 'Country-year aggregates from official ACLED files';
COMMENT ON TABLE acled_aggregated.country_month_year IS 'Country-month-year aggregates';
COMMENT ON TABLE acled_aggregated.regional IS 'Regional aggregates with flexible temporal/spatial granularity';

COMMIT;
