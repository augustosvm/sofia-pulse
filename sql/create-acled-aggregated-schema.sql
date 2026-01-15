-- ============================================================================
-- ACLED Aggregated Data Schema
-- ============================================================================
-- Purpose: Store OFFICIAL aggregated datasets from ACLED
-- CRITICAL: These are NOT derived from event-level data
--           These are OFFICIAL published aggregates
-- ============================================================================

-- Create schemas
CREATE SCHEMA IF NOT EXISTS acled_aggregated;
CREATE SCHEMA IF NOT EXISTS acled_metadata;

-- ============================================================================
-- Metadata Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS acled_metadata.datasets (
    id SERIAL PRIMARY KEY,
    dataset_slug VARCHAR(255) UNIQUE NOT NULL,
    source_url TEXT NOT NULL,
    download_url TEXT,
    aggregation_level VARCHAR(100) NOT NULL, -- country-year, admin1-week, etc
    region VARCHAR(100),
    file_hash VARCHAR(64) NOT NULL, -- SHA256
    file_name VARCHAR(500),
    file_size_bytes BIGINT,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_aggregated BOOLEAN DEFAULT TRUE,
    source_type VARCHAR(100) DEFAULT 'ACLED_OFFICIAL_AGGREGATE',
    detected_columns JSONB, -- Store detected column structure
    version_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_datasets_slug ON acled_metadata.datasets(dataset_slug);
CREATE INDEX idx_datasets_hash ON acled_metadata.datasets(file_hash);
CREATE INDEX idx_datasets_collected ON acled_metadata.datasets(collected_at);

-- ============================================================================
-- Aggregated Data Tables
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
    metadata JSONB, -- Store any additional columns
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

-- Regional Aggregates (flexible structure)
CREATE TABLE IF NOT EXISTS acled_aggregated.regional (
    id SERIAL PRIMARY KEY,
    dataset_slug VARCHAR(255) NOT NULL,
    region VARCHAR(100) NOT NULL,
    country VARCHAR(255),
    admin1 VARCHAR(255),
    year INT,
    month INT,
    week INT,
    date_range_start DATE,
    date_range_end DATE,
    events INT,
    fatalities INT,
    event_type VARCHAR(100),
    metadata JSONB, -- Flexible storage for region-specific columns
    source_file_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(dataset_slug, region, country, admin1, year, month, week, event_type, source_file_hash)
);

CREATE INDEX idx_regional_region ON acled_aggregated.regional(region);
CREATE INDEX idx_regional_country ON acled_aggregated.regional(country);
CREATE INDEX idx_regional_year ON acled_aggregated.regional(year);

-- ============================================================================
-- Helper Views
-- ============================================================================

-- Latest version of each dataset
CREATE OR REPLACE VIEW acled_metadata.latest_datasets AS
SELECT DISTINCT ON (dataset_slug)
    *
FROM acled_metadata.datasets
ORDER BY dataset_slug, collected_at DESC;

-- Summary by aggregation level
CREATE OR REPLACE VIEW acled_metadata.aggregation_summary AS
SELECT 
    aggregation_level,
    COUNT(*) as dataset_count,
    MAX(collected_at) as last_collected,
    SUM(file_size_bytes) as total_size_bytes
FROM acled_metadata.datasets
GROUP BY aggregation_level;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON SCHEMA acled_aggregated IS 'Official ACLED aggregated datasets - NOT derived from events';
COMMENT ON SCHEMA acled_metadata IS 'Metadata tracking for ACLED aggregate collection';

COMMENT ON TABLE acled_metadata.datasets IS 'Tracking table for all collected ACLED aggregated datasets';
COMMENT ON TABLE acled_aggregated.country_year IS 'Country-year level aggregates from ACLED official files';
COMMENT ON TABLE acled_aggregated.country_month_year IS 'Country-month-year level aggregates';
COMMENT ON TABLE acled_aggregated.regional IS 'Regional aggregates with flexible temporal granularity';

COMMENT ON COLUMN acled_metadata.datasets.source_type IS 'Always ACLED_OFFICIAL_AGGREGATE to distinguish from derived data';
COMMENT ON COLUMN acled_metadata.datasets.is_aggregated IS 'Always TRUE - these are aggregate datasets';
COMMENT ON COLUMN acled_aggregated.country_year.metadata IS 'JSONB storage for dataset-specific additional columns';
