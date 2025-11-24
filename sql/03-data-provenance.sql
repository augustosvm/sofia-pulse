-- ============================================================================
-- DATA PROVENANCE - Metadata & Transparency System
-- ============================================================================
-- Purpose: Track metadata about all data sources for:
--   - Product sales (show customers where data comes from)
--   - Portal display (attribution, licensing)
--   - Auditing (verify data quality and freshness)
--   - Journalist queries (cite sources properly)
--   - Legal compliance (track licenses)
-- ============================================================================

-- Create license types enum
CREATE TYPE sofia.license_type AS ENUM (
    'CC0',                  -- Public domain
    'CC_BY',                -- Creative Commons Attribution
    'CC_BY_SA',             -- CC Attribution-ShareAlike
    'CC_BY_NC',             -- CC Attribution-NonCommercial
    'CC_BY_NC_SA',          -- CC Attribution-NonCommercial-ShareAlike
    'ODbL',                 -- Open Database License
    'GOVT_PUBLIC',          -- Government public data
    'PROPRIETARY',          -- Proprietary/restricted
    'MIT',                  -- MIT License
    'APACHE',               -- Apache 2.0
    'GPL',                  -- GNU GPL
    'CUSTOM',               -- Custom license
    'UNKNOWN'               -- Unknown/not specified
);

-- Create data quality levels enum
CREATE TYPE sofia.quality_level AS ENUM (
    'VERIFIED',             -- Manually verified, high quality
    'VALIDATED',            -- Automatically validated
    'GOOD',                 -- Good quality, minor issues
    'FAIR',                 -- Fair quality, some issues
    'POOR',                 -- Poor quality, many issues
    'UNKNOWN'               -- Not yet assessed
);

-- Create update frequency enum
CREATE TYPE sofia.update_frequency AS ENUM (
    'REALTIME',             -- Real-time (streaming)
    'MINUTELY',             -- Every minute
    'HOURLY',               -- Every hour
    'DAILY',                -- Daily
    'WEEKLY',               -- Weekly
    'MONTHLY',              -- Monthly
    'QUARTERLY',            -- Quarterly
    'YEARLY',               -- Yearly
    'ONCE',                 -- One-time snapshot
    'IRREGULAR',            -- Irregular/on-demand
    'UNKNOWN'               -- Unknown frequency
);

-- Main data sources registry
CREATE TABLE IF NOT EXISTS sofia.data_sources (
    source_id TEXT PRIMARY KEY,             -- Unique identifier (e.g., 'world_bank', 'github', 'arxiv')

    -- Basic information
    source_name TEXT NOT NULL,              -- Human-readable name (e.g., "World Bank Gender Data Portal")
    source_category TEXT NOT NULL,          -- Category (e.g., 'economic', 'social', 'tech', 'health')
    description TEXT,                       -- Description of data source

    -- URLs and endpoints
    source_url TEXT,                        -- Main website URL
    api_endpoint TEXT,                      -- API endpoint (if applicable)
    documentation_url TEXT,                 -- Documentation URL
    terms_of_use_url TEXT,                  -- Terms of service URL

    -- Licensing
    license_type sofia.license_type NOT NULL DEFAULT 'UNKNOWN',
    license_text TEXT,                      -- Full license text or summary
    commercial_use_allowed BOOLEAN,         -- Can be used commercially
    attribution_required BOOLEAN DEFAULT true,
    attribution_text TEXT,                  -- How to cite this source

    -- Collection metadata
    collection_method TEXT,                 -- 'api', 'scraping', 'download', 'manual'
    update_frequency sofia.update_frequency DEFAULT 'UNKNOWN',
    last_updated TIMESTAMP,                 -- Last time source data was updated
    next_update_expected TIMESTAMP,         -- Expected next update

    -- Data quality
    quality_level sofia.quality_level DEFAULT 'UNKNOWN',
    data_quality_score FLOAT,               -- 0.0-1.0 quality score
    completeness_pct FLOAT,                 -- % of expected data present
    accuracy_pct FLOAT,                     -- % of accurate data (validated)
    quality_issues TEXT[],                  -- List of known quality issues

    -- Coverage
    geographic_coverage TEXT[],             -- Countries/regions covered
    temporal_coverage_start DATE,           -- Start of time coverage
    temporal_coverage_end DATE,             -- End of time coverage
    record_count BIGINT,                    -- Approximate number of records

    -- Reliability
    uptime_pct FLOAT,                       -- API uptime % (last 30d)
    error_rate FLOAT,                       -- Error rate (0.0-1.0)
    avg_response_time_ms INTEGER,           -- Average API response time

    -- Contact
    provider_name TEXT,                     -- Data provider organization
    provider_contact TEXT,                  -- Contact email/URL
    maintainer TEXT,                        -- Sofia team member responsible

    -- Metadata
    tags TEXT[] DEFAULT '{}',               -- Searchable tags
    metadata JSONB DEFAULT '{}',            -- Flexible metadata

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_quality_score CHECK (data_quality_score IS NULL OR (data_quality_score >= 0 AND data_quality_score <= 1)),
    CONSTRAINT valid_completeness CHECK (completeness_pct IS NULL OR (completeness_pct >= 0 AND completeness_pct <= 100)),
    CONSTRAINT valid_accuracy CHECK (accuracy_pct IS NULL OR (accuracy_pct >= 0 AND accuracy_pct <= 100)),
    CONSTRAINT valid_uptime CHECK (uptime_pct IS NULL OR (uptime_pct >= 0 AND uptime_pct <= 100)),
    CONSTRAINT valid_error_rate CHECK (error_rate IS NULL OR (error_rate >= 0 AND error_rate <= 1))
);

-- Create indexes
CREATE INDEX idx_data_sources_category ON sofia.data_sources(source_category);
CREATE INDEX idx_data_sources_license ON sofia.data_sources(license_type);
CREATE INDEX idx_data_sources_quality ON sofia.data_sources(quality_level);
CREATE INDEX idx_data_sources_update_freq ON sofia.data_sources(update_frequency);
CREATE INDEX idx_data_sources_commercial ON sofia.data_sources(commercial_use_allowed);

-- GIN indexes
CREATE INDEX idx_data_sources_tags ON sofia.data_sources USING GIN(tags);
CREATE INDEX idx_data_sources_geo_coverage ON sofia.data_sources USING GIN(geographic_coverage);

COMMENT ON TABLE sofia.data_sources IS 'Registry of all data sources with licensing, quality, and provenance metadata';

-- ============================================================================
-- TABLE-LEVEL PROVENANCE
-- ============================================================================

-- Links database tables to their sources
CREATE TABLE IF NOT EXISTS sofia.table_provenance (
    table_name TEXT PRIMARY KEY,            -- Table name in sofia schema
    source_id TEXT NOT NULL REFERENCES sofia.data_sources(source_id),

    -- Collection details
    collector_script TEXT,                  -- Script that populates this table
    last_collection_run TIMESTAMP,          -- Last successful collection
    next_collection_scheduled TIMESTAMP,    -- Next scheduled collection

    -- Data statistics
    current_record_count BIGINT,            -- Current number of records
    total_records_collected BIGINT,         -- Total records ever collected
    avg_records_per_run BIGINT,             -- Average records per collection run
    oldest_record_date TIMESTAMP,           -- Oldest record in table
    newest_record_date TIMESTAMP,           -- Newest record in table

    -- Health metrics
    collection_success_rate FLOAT,          -- % of successful collections
    avg_collection_duration_sec INTEGER,    -- Average collection time
    last_error TEXT,                        -- Last error encountered
    error_count_30d INTEGER DEFAULT 0,      -- Errors in last 30 days

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_success_rate CHECK (collection_success_rate IS NULL OR (collection_success_rate >= 0 AND collection_success_rate <= 1))
);

CREATE INDEX idx_table_provenance_source ON sofia.table_provenance(source_id);
CREATE INDEX idx_table_provenance_last_run ON sofia.table_provenance(last_collection_run DESC);

COMMENT ON TABLE sofia.table_provenance IS 'Links database tables to their data sources - tracks collection health';

-- ============================================================================
-- COLUMN-LEVEL PROVENANCE
-- ============================================================================

-- Tracks provenance for specific columns
CREATE TABLE IF NOT EXISTS sofia.column_provenance (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sofia.data_sources(source_id),

    -- Mapping
    source_field TEXT,                      -- Original field name in source
    transformation TEXT,                    -- Transformation applied (if any)

    -- Quality
    null_percentage FLOAT,                  -- % of NULL values
    unique_percentage FLOAT,                -- % of unique values
    quality_issues TEXT[],                  -- Known quality issues for this column

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(table_name, column_name),
    CONSTRAINT valid_null_pct CHECK (null_percentage IS NULL OR (null_percentage >= 0 AND null_percentage <= 100)),
    CONSTRAINT valid_unique_pct CHECK (unique_percentage IS NULL OR (unique_percentage >= 0 AND unique_percentage <= 100))
);

CREATE INDEX idx_column_provenance_table ON sofia.column_provenance(table_name);
CREATE INDEX idx_column_provenance_source ON sofia.column_provenance(source_id);

COMMENT ON TABLE sofia.column_provenance IS 'Column-level provenance - tracks source and quality of individual columns';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to register a data source
CREATE OR REPLACE FUNCTION sofia.register_data_source(
    p_source_id TEXT,
    p_source_name TEXT,
    p_source_category TEXT,
    p_license_type TEXT,
    p_source_url TEXT DEFAULT NULL,
    p_commercial_use_allowed BOOLEAN DEFAULT NULL,
    p_attribution_text TEXT DEFAULT NULL,
    p_update_frequency TEXT DEFAULT 'UNKNOWN'
)
RETURNS TEXT AS $$
BEGIN
    INSERT INTO sofia.data_sources (
        source_id,
        source_name,
        source_category,
        license_type,
        source_url,
        commercial_use_allowed,
        attribution_text,
        update_frequency
    ) VALUES (
        p_source_id,
        p_source_name,
        p_source_category,
        p_license_type::sofia.license_type,
        p_source_url,
        p_commercial_use_allowed,
        p_attribution_text,
        p_update_frequency::sofia.update_frequency
    )
    ON CONFLICT (source_id) DO UPDATE SET
        source_name = EXCLUDED.source_name,
        source_category = EXCLUDED.source_category,
        license_type = EXCLUDED.license_type,
        source_url = EXCLUDED.source_url,
        commercial_use_allowed = EXCLUDED.commercial_use_allowed,
        attribution_text = EXCLUDED.attribution_text,
        update_frequency = EXCLUDED.update_frequency,
        updated_at = NOW();

    RETURN p_source_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.register_data_source IS 'Register or update a data source in the registry';

-- Function to link table to source
CREATE OR REPLACE FUNCTION sofia.link_table_to_source(
    p_table_name TEXT,
    p_source_id TEXT,
    p_collector_script TEXT DEFAULT NULL
)
RETURNS TEXT AS $$
BEGIN
    INSERT INTO sofia.table_provenance (
        table_name,
        source_id,
        collector_script
    ) VALUES (
        p_table_name,
        p_source_id,
        p_collector_script
    )
    ON CONFLICT (table_name) DO UPDATE SET
        source_id = EXCLUDED.source_id,
        collector_script = EXCLUDED.collector_script,
        updated_at = NOW();

    RETURN p_table_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.link_table_to_source IS 'Link a database table to its data source';

-- Function to update table statistics
CREATE OR REPLACE FUNCTION sofia.update_table_statistics(
    p_table_name TEXT
)
RETURNS VOID AS $$
DECLARE
    v_count BIGINT;
BEGIN
    -- Get current record count
    EXECUTE format('SELECT COUNT(*) FROM sofia.%I', p_table_name) INTO v_count;

    -- Update provenance
    UPDATE sofia.table_provenance
    SET current_record_count = v_count,
        updated_at = NOW()
    WHERE table_name = p_table_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.update_table_statistics IS 'Update statistics for a table (call after collection runs)';

-- Function to get attribution text for a table
CREATE OR REPLACE FUNCTION sofia.get_attribution(
    p_table_name TEXT
)
RETURNS TEXT AS $$
DECLARE
    v_attribution TEXT;
BEGIN
    SELECT ds.attribution_text INTO v_attribution
    FROM sofia.table_provenance tp
    JOIN sofia.data_sources ds ON tp.source_id = ds.source_id
    WHERE tp.table_name = p_table_name;

    IF v_attribution IS NULL THEN
        RETURN 'Data source attribution not available';
    END IF;

    RETURN v_attribution;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.get_attribution IS 'Get attribution text for a table - use in reports/exports';

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- View: Sources summary
CREATE OR REPLACE VIEW sofia.sources_summary AS
SELECT
    source_id,
    source_name,
    source_category,
    license_type,
    commercial_use_allowed,
    quality_level,
    update_frequency,
    record_count,
    last_updated,
    uptime_pct,
    data_quality_score
FROM sofia.data_sources
ORDER BY source_category, source_name;

-- View: Tables by source
CREATE OR REPLACE VIEW sofia.tables_by_source AS
SELECT
    ds.source_id,
    ds.source_name,
    ds.license_type,
    ds.commercial_use_allowed,
    tp.table_name,
    tp.current_record_count,
    tp.last_collection_run,
    tp.collection_success_rate
FROM sofia.data_sources ds
LEFT JOIN sofia.table_provenance tp ON ds.source_id = tp.source_id
ORDER BY ds.source_name, tp.table_name;

-- View: Commercial-use sources
CREATE OR REPLACE VIEW sofia.commercial_sources AS
SELECT
    source_id,
    source_name,
    license_type,
    attribution_text,
    COUNT(*) FILTER (WHERE tp.table_name IS NOT NULL) as table_count,
    SUM(tp.current_record_count) as total_records
FROM sofia.data_sources ds
LEFT JOIN sofia.table_provenance tp ON ds.source_id = tp.source_id
WHERE commercial_use_allowed = true
GROUP BY source_id, source_name, license_type, attribution_text
ORDER BY total_records DESC NULLS LAST;

-- View: Data quality dashboard
CREATE OR REPLACE VIEW sofia.data_quality_dashboard AS
SELECT
    ds.source_id,
    ds.source_name,
    ds.quality_level,
    ds.data_quality_score,
    tp.table_name,
    tp.current_record_count,
    tp.collection_success_rate,
    tp.error_count_30d,
    ds.uptime_pct
FROM sofia.data_sources ds
LEFT JOIN sofia.table_provenance tp ON ds.source_id = tp.source_id
ORDER BY ds.data_quality_score DESC NULLS LAST;

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT ON sofia.data_sources TO PUBLIC;
GRANT SELECT ON sofia.table_provenance TO PUBLIC;
GRANT SELECT ON sofia.column_provenance TO PUBLIC;
GRANT SELECT ON sofia.sources_summary TO PUBLIC;
GRANT SELECT ON sofia.tables_by_source TO PUBLIC;
GRANT SELECT ON sofia.commercial_sources TO PUBLIC;
GRANT SELECT ON sofia.data_quality_dashboard TO PUBLIC;

-- ============================================================================
-- COMPLETE
-- ============================================================================

SELECT 'Data Provenance system created successfully!' as status;
