-- ============================================================================
-- Migration 015: Data Normalization Layer (Enterprise)
-- Purpose: Indexed, deterministic geo-mapping infra (performance fix)
-- ============================================================================

-- Optional (recommended): trigram extension for fuzzy matching
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ----------------------------------------------------------------------------
-- 1) COUNTRY ALIASES
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS sofia.country_aliases;

CREATE TABLE sofia.country_aliases (
    id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL REFERENCES sofia.countries(iso_alpha2) ON UPDATE CASCADE,
    alias TEXT NOT NULL,
    alias_norm TEXT NOT NULL,
    alias_type TEXT NOT NULL DEFAULT 'common', -- common, official, variant, demonym
    UNIQUE(country_code, alias_norm)
);

-- Normalize helper: lowercase + remove punctuation/spaces
-- We store alias_norm at insert time to keep queries cheap.
INSERT INTO sofia.country_aliases (country_code, alias, alias_norm, alias_type)
SELECT
    iso_alpha2,
    common_name,
    regexp_replace(lower(common_name), '[^a-z0-9]+', '', 'g') as alias_norm,
    'common'
FROM sofia.countries
WHERE iso_alpha2 IS NOT NULL AND common_name IS NOT NULL
ON CONFLICT DO NOTHING;

-- If official_name exists
INSERT INTO sofia.country_aliases (country_code, alias, alias_norm, alias_type)
SELECT
    iso_alpha2,
    official_name,
    regexp_replace(lower(official_name), '[^a-z0-9]+', '', 'g') as alias_norm,
    'official'
FROM sofia.countries
WHERE iso_alpha2 IS NOT NULL AND official_name IS NOT NULL AND official_name != common_name
ON CONFLICT DO NOTHING;

-- Hardcoded variants (high-signal only)
INSERT INTO sofia.country_aliases (country_code, alias, alias_norm, alias_type) VALUES
('US','USA','usa','variant'),
('US','United States of America','unitedstatesofamerica','variant'),
('US','U.S.','us','variant'),
('US','U.S.A.','usa','variant'),
('GB','UK','uk','variant'),
('GB','U.K.','uk','variant'),
('GB','Britain','britain','variant'),
('GB','United Kingdom','unitedkingdom','variant'),
('GB','England','england','variant'),
('BR','Brasil','brasil','variant'),
('RU','Russia','russia','common'),
('RU','Russian Federation','russianfederation','official'),
('CN','China','china','common'),
('CN','PRC','prc','variant'),
('DE','Germany','germany','common'),
('DE','Deutschland','deutschland','variant'),
('FR','France','france','common'),
('JP','Japan','japan','common'),
('IN','India','india','common'),
('KR','South Korea','southkorea','common'),
('KR','Korea','korea','variant'),
('AU','Australia','australia','common'),
('CA','Canada','canada','common'),
('IL','Israel','israel','common'),
('SG','Singapore','singapore','common'),
('NL','Netherlands','netherlands','common'),
('NL','Holland','holland','variant'),
('CH','Switzerland','switzerland','common'),
('SE','Sweden','sweden','common'),
('ES','Spain','spain','common'),
('IT','Italy','italy','common'),
('MX','Mexico','mexico','common'),
('AR','Argentina','argentina','common'),
('ZA','South Africa','southafrica','common'),
('AE','UAE','uae','variant'),
('AE','United Arab Emirates','unitedarabemirates','official'),
('SA','Saudi Arabia','saudiarabia','common'),
('TW','Taiwan','taiwan','common'),
('HK','Hong Kong','hongkong','common'),
('PL','Poland','poland','common'),
('ID','Indonesia','indonesia','common'),
('TH','Thailand','thailand','common'),
('VN','Vietnam','vietnam','common'),
('PH','Philippines','philippines','common'),
('MY','Malaysia','malaysia','common'),
('NZ','New Zealand','newzealand','common'),
('IE','Ireland','ireland','common'),
('AT','Austria','austria','common'),
('BE','Belgium','belgium','common'),
('DK','Denmark','denmark','common'),
('FI','Finland','finland','common'),
('NO','Norway','norway','common'),
('PT','Portugal','portugal','common'),
('CZ','Czechia','czechia','variant'),
('CZ','Czech Republic','czechrepublic','common'),
('GR','Greece','greece','common'),
('HU','Hungary','hungary','common'),
('RO','Romania','romania','common'),
('UA','Ukraine','ukraine','common'),
('EG','Egypt','egypt','common'),
('NG','Nigeria','nigeria','common'),
('KE','Kenya','kenya','common'),
('CO','Colombia','colombia','common'),
('CL','Chile','chile','common'),
('PE','Peru','peru','common')
ON CONFLICT DO NOTHING;

CREATE INDEX idx_country_aliases_norm ON sofia.country_aliases(alias_norm);
CREATE INDEX idx_country_aliases_code ON sofia.country_aliases(country_code);

-- If pg_trgm enabled:
-- CREATE INDEX idx_country_aliases_norm_trgm ON sofia.country_aliases USING gin (alias_norm gin_trgm_ops);

COMMENT ON TABLE sofia.country_aliases IS 'Canonical alias set for deterministic/fuzzy country matching';

-- ----------------------------------------------------------------------------
-- 2) SIGNAL COUNTRY MAP
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS sofia.signal_country_map;

CREATE TABLE sofia.signal_country_map (
    signal_id BIGINT PRIMARY KEY,
    country_code CHAR(2) NOT NULL REFERENCES sofia.countries(iso_alpha2) ON UPDATE CASCADE,
    match_method TEXT NOT NULL, -- metadata_jurisdiction, metadata_country_code, url_tld, alias_exact, manual
    confidence_hint NUMERIC(3,2) NOT NULL DEFAULT 0.70,
    matched_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signal_map_country ON sofia.signal_country_map(country_code);

-- ----------------------------------------------------------------------------
-- 3) CYBER EVENT COUNTRY MAP
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS sofia.cyber_event_country_map;

CREATE TABLE sofia.cyber_event_country_map (
    event_id BIGINT PRIMARY KEY REFERENCES sofia.cybersecurity_events(id) ON DELETE CASCADE,
    country_code CHAR(2) NOT NULL REFERENCES sofia.countries(iso_alpha2) ON UPDATE CASCADE,
    match_method TEXT NOT NULL, -- alias_exact, alias_fuzzy, source_domain, manual
    confidence_hint NUMERIC(3,2) NOT NULL DEFAULT 0.50,
    matched_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cyber_map_country ON sofia.cyber_event_country_map(country_code);

-- ----------------------------------------------------------------------------
-- 4) TRIAL COUNTRY MAP
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS sofia.trial_country_map;

CREATE TABLE sofia.trial_country_map (
    nct_id VARCHAR(20) PRIMARY KEY,
    country_code CHAR(2) NOT NULL REFERENCES sofia.countries(iso_alpha2) ON UPDATE CASCADE,
    match_method TEXT NOT NULL, -- sponsor_country_field, sponsor_alias, org_join, manual
    confidence_hint NUMERIC(3,2) NOT NULL DEFAULT 0.50,
    matched_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trial_map_country ON sofia.trial_country_map(country_code);

-- ----------------------------------------------------------------------------
-- COMMENTS
-- ----------------------------------------------------------------------------
COMMENT ON TABLE sofia.signal_country_map IS 'Pre-computed signal->country mapping (backfilled, FK validated)';
COMMENT ON TABLE sofia.cyber_event_country_map IS 'Pre-computed event->country mapping (backfilled, FK validated)';
COMMENT ON TABLE sofia.trial_country_map IS 'Pre-computed trial->country mapping (backfilled, FK validated)';
