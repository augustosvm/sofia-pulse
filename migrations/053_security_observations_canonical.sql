-- Security Hybrid Model - Canonical Table
-- Migration: 053_security_observations_canonical.sql
-- Date: 2026-01-15
-- Purpose: Create unified security observations table for hybrid model

-- ============================================================================
-- 1. CREATE CANONICAL TABLE
-- ============================================================================

DROP TABLE IF EXISTS sofia.security_observations CASCADE;

CREATE TABLE sofia.security_observations (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Source Identification
    source VARCHAR(50) NOT NULL CHECK (source IN (
        'ACLED', 'GDELT', 'WORLD_BANK',
        'BRASIL_CRIME', 'BRASIL_VIOLENCE_WOMEN', 'BRASIL_ONG_IPEA', 'BRASIL_GOV_DATASUS',
        'MSF', 'UNHCR', 'WHO', 'UNICEF'
    )),
    source_id VARCHAR(200) UNIQUE,
    
    -- Signal Classification
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN (
        'acute', 'structural', 'humanitarian', 'local'
    )),
    coverage_scope VARCHAR(30) NOT NULL CHECK (coverage_scope IN (
        'global_comparable', 'local_only', 'thematic_only'
    )),
    
    -- Geographic Information
    country_code VARCHAR(10),
    country_name VARCHAR(200),
    admin1 VARCHAR(200),
    city VARCHAR(200),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    
    -- Severity & Confidence
    severity_raw DECIMAL(15, 2),
    severity_norm DECIMAL(5, 2) CHECK (severity_norm >= 0 AND severity_norm <= 100),
    confidence_score DECIMAL(5, 2) CHECK (confidence_score >= 0 AND confidence_score <= 100),
    
    -- Coverage Scores
    coverage_score_global DECIMAL(5, 2) CHECK (coverage_score_global >= 0 AND coverage_score_global <= 100),
    coverage_score_local DECIMAL(5, 2) CHECK (coverage_score_local >= 0 AND coverage_score_local <= 100),
    
    -- Temporal Information
    event_time_start DATE,
    event_time_end DATE,
    
    -- Event Metrics
    event_count INTEGER DEFAULT 1,
    fatalities INTEGER DEFAULT 0,
    
    -- Raw Data
    raw_payload JSONB,
    
    -- Metadata
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. CREATE INDEXES
-- ============================================================================

CREATE INDEX idx_security_obs_source ON sofia.security_observations(source);
CREATE INDEX idx_security_obs_signal_type ON sofia.security_observations(signal_type);
CREATE INDEX idx_security_obs_coverage_scope ON sofia.security_observations(coverage_scope);
CREATE INDEX idx_security_obs_country_code ON sofia.security_observations(country_code);
CREATE INDEX idx_security_obs_country_name ON sofia.security_observations(country_name);
CREATE INDEX idx_security_obs_time_start ON sofia.security_observations(event_time_start);
CREATE INDEX idx_security_obs_severity_norm ON sofia.security_observations(severity_norm DESC);
CREATE INDEX idx_security_obs_coverage_global ON sofia.security_observations(coverage_score_global DESC);

-- Composite indexes for common queries
CREATE INDEX idx_security_obs_source_country ON sofia.security_observations(source, country_code);
CREATE INDEX idx_security_obs_signal_country ON sofia.security_observations(signal_type, country_code);
CREATE INDEX idx_security_obs_geo ON sofia.security_observations(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ============================================================================
-- 3. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate coverage score
CREATE OR REPLACE FUNCTION sofia.calculate_coverage_score(
    p_country_code VARCHAR,
    p_scope VARCHAR
) RETURNS DECIMAL AS $$
DECLARE
    v_source_count INTEGER;
    v_recency_days INTEGER;
    v_granularity VARCHAR;
    v_score DECIMAL;
BEGIN
    -- Count distinct sources for this country
    SELECT COUNT(DISTINCT source)
    INTO v_source_count
    FROM sofia.security_observations
    WHERE country_code = p_country_code
      AND coverage_scope = p_scope
      AND event_time_start >= CURRENT_DATE - INTERVAL '90 days';
    
    -- Get most recent data age
    SELECT EXTRACT(DAY FROM CURRENT_DATE - MAX(event_time_start))
    INTO v_recency_days
    FROM sofia.security_observations
    WHERE country_code = p_country_code
      AND coverage_scope = p_scope;
    
    -- Determine granularity
    SELECT CASE
        WHEN COUNT(*) FILTER (WHERE city IS NOT NULL) > 0 THEN 'city'
        WHEN COUNT(*) FILTER (WHERE admin1 IS NOT NULL) > 0 THEN 'admin'
        ELSE 'country'
    END
    INTO v_granularity
    FROM sofia.security_observations
    WHERE country_code = p_country_code
      AND coverage_scope = p_scope;
    
    -- Calculate score
    v_score := CASE
        WHEN v_source_count >= 3 AND v_recency_days < 30 AND v_granularity = 'city' THEN 100
        WHEN v_source_count >= 2 AND v_recency_days < 60 AND v_granularity = 'admin' THEN 75
        WHEN v_source_count >= 1 AND v_recency_days < 90 AND v_granularity = 'country' THEN 50
        ELSE 25
    END;
    
    RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Function to update coverage scores
CREATE OR REPLACE FUNCTION sofia.update_coverage_scores()
RETURNS void AS $$
BEGIN
    -- Update global coverage scores
    UPDATE sofia.security_observations
    SET coverage_score_global = sofia.calculate_coverage_score(country_code, 'global_comparable')
    WHERE coverage_scope = 'global_comparable';
    
    -- Update local coverage scores
    UPDATE sofia.security_observations
    SET coverage_score_local = sofia.calculate_coverage_score(country_code, 'local_only')
    WHERE coverage_scope = 'local_only';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. CREATE TRIGGER FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION sofia.update_security_observations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_security_observations_timestamp
    BEFORE UPDATE ON sofia.security_observations
    FOR EACH ROW
    EXECUTE FUNCTION sofia.update_security_observations_timestamp();

-- ============================================================================
-- 5. COMMENTS
-- ============================================================================

COMMENT ON TABLE sofia.security_observations IS 'Canonical security observations from all sources (ACLED, GDELT, World Bank, Brasil, ONGs)';
COMMENT ON COLUMN sofia.security_observations.source IS 'Data source identifier';
COMMENT ON COLUMN sofia.security_observations.signal_type IS 'Type of security signal: acute (conflicts), structural (indicators), humanitarian (crises), local (high-res local data)';
COMMENT ON COLUMN sofia.security_observations.coverage_scope IS 'Comparability scope: global_comparable, local_only, thematic_only';
COMMENT ON COLUMN sofia.security_observations.severity_norm IS 'Normalized severity score 0-100';
COMMENT ON COLUMN sofia.security_observations.confidence_score IS 'Data confidence/quality score 0-100';
COMMENT ON COLUMN sofia.security_observations.coverage_score_global IS 'Global coverage quality score 0-100';
COMMENT ON COLUMN sofia.security_observations.coverage_score_local IS 'Local coverage quality score 0-100';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
