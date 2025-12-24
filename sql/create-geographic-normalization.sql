-- Normalização Geográfica - Estrutura Base
-- Criação de tabelas master para países, estados e cidades

-- 1. TABELA DE PAÍSES
CREATE TABLE IF NOT EXISTS sofia.countries (
    id SERIAL PRIMARY KEY,
    common_name VARCHAR(200) UNIQUE NOT NULL,
    official_name VARCHAR(300),
    iso_alpha2 CHAR(2) UNIQUE,
    iso_alpha3 CHAR(3) UNIQUE,
    region VARCHAR(100),
    subregion VARCHAR(100),
    population BIGINT,
    area NUMERIC,
    capital VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TABELA DE ESTADOS/PROVÍNCIAS
CREATE TABLE IF NOT EXISTS sofia.states (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(10),
    country_id INTEGER NOT NULL REFERENCES sofia.countries(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, country_id)
);

-- 3. TABELA DE CIDADES
CREATE TABLE IF NOT EXISTS sofia.cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    state_id INTEGER REFERENCES sofia.states(id) ON DELETE SET NULL,
    country_id INTEGER NOT NULL REFERENCES sofia.countries(id) ON DELETE CASCADE,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    population INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, state_id, country_id)
);

-- ÍNDICES PARA PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_countries_common_name ON sofia.countries(common_name);
CREATE INDEX IF NOT EXISTS idx_countries_iso2 ON sofia.countries(iso_alpha2);
CREATE INDEX IF NOT EXISTS idx_countries_iso3 ON sofia.countries(iso_alpha3);
CREATE INDEX IF NOT EXISTS idx_countries_region ON sofia.countries(region);

CREATE INDEX IF NOT EXISTS idx_states_name ON sofia.states(name);
CREATE INDEX IF NOT EXISTS idx_states_country ON sofia.states(country_id);
CREATE INDEX IF NOT EXISTS idx_states_code ON sofia.states(code);

CREATE INDEX IF NOT EXISTS idx_cities_name ON sofia.cities(name);
CREATE INDEX IF NOT EXISTS idx_cities_state ON sofia.cities(state_id);
CREATE INDEX IF NOT EXISTS idx_cities_country ON sofia.cities(country_id);
CREATE INDEX IF NOT EXISTS idx_cities_coords ON sofia.cities(latitude, longitude);

-- POPULAR PAÍSES PRINCIPAIS (Top 50 mais relevantes)
INSERT INTO sofia.countries (common_name, official_name, iso_alpha2, iso_alpha3, region, subregion) VALUES
('United States', 'United States of America', 'US', 'USA', 'Americas', 'Northern America'),
('Brazil', 'Federative Republic of Brazil', 'BR', 'BRA', 'Americas', 'South America'),
('United Kingdom', 'United Kingdom of Great Britain and Northern Ireland', 'GB', 'GBR', 'Europe', 'Northern Europe'),
('Canada', 'Canada', 'CA', 'CAN', 'Americas', 'Northern America'),
('Australia', 'Commonwealth of Australia', 'AU', 'AUS', 'Oceania', 'Australia and New Zealand'),
('Germany', 'Federal Republic of Germany', 'DE', 'DEU', 'Europe', 'Western Europe'),
('France', 'French Republic', 'FR', 'FRA', 'Europe', 'Western Europe'),
('India', 'Republic of India', 'IN', 'IND', 'Asia', 'Southern Asia'),
('China', 'People''s Republic of China', 'CN', 'CHN', 'Asia', 'Eastern Asia'),
('Japan', 'Japan', 'JP', 'JPN', 'Asia', 'Eastern Asia'),
('Mexico', 'United Mexican States', 'MX', 'MEX', 'Americas', 'Central America'),
('Spain', 'Kingdom of Spain', 'ES', 'ESP', 'Europe', 'Southern Europe'),
('Italy', 'Italian Republic', 'IT', 'ITA', 'Europe', 'Southern Europe'),
('Netherlands', 'Kingdom of the Netherlands', 'NL', 'NLD', 'Europe', 'Western Europe'),
('Singapore', 'Republic of Singapore', 'SG', 'SGP', 'Asia', 'South-Eastern Asia'),
('South Korea', 'Republic of Korea', 'KR', 'KOR', 'Asia', 'Eastern Asia'),
('Argentina', 'Argentine Republic', 'AR', 'ARG', 'Americas', 'South America'),
('Chile', 'Republic of Chile', 'CL', 'CHL', 'Americas', 'South America'),
('Colombia', 'Republic of Colombia', 'CO', 'COL', 'Americas', 'South America'),
('Peru', 'Republic of Peru', 'PE', 'PER', 'Americas', 'South America'),
('Portugal', 'Portuguese Republic', 'PT', 'PRT', 'Europe', 'Southern Europe'),
('Poland', 'Republic of Poland', 'PL', 'POL', 'Europe', 'Eastern Europe'),
('Sweden', 'Kingdom of Sweden', 'SE', 'SWE', 'Europe', 'Northern Europe'),
('Norway', 'Kingdom of Norway', 'NO', 'NOR', 'Europe', 'Northern Europe'),
('Denmark', 'Kingdom of Denmark', 'DK', 'DNK', 'Europe', 'Northern Europe'),
('Finland', 'Republic of Finland', 'FI', 'FIN', 'Europe', 'Northern Europe'),
('Switzerland', 'Swiss Confederation', 'CH', 'CHE', 'Europe', 'Western Europe'),
('Austria', 'Republic of Austria', 'AT', 'AUT', 'Europe', 'Western Europe'),
('Belgium', 'Kingdom of Belgium', 'BE', 'BEL', 'Europe', 'Western Europe'),
('Ireland', 'Republic of Ireland', 'IE', 'IRL', 'Europe', 'Northern Europe'),
('New Zealand', 'New Zealand', 'NZ', 'NZL', 'Oceania', 'Australia and New Zealand'),
('South Africa', 'Republic of South Africa', 'ZA', 'ZAF', 'Africa', 'Southern Africa'),
('Israel', 'State of Israel', 'IL', 'ISR', 'Asia', 'Western Asia'),
('United Arab Emirates', 'United Arab Emirates', 'AE', 'ARE', 'Asia', 'Western Asia'),
('Saudi Arabia', 'Kingdom of Saudi Arabia', 'SA', 'SAU', 'Asia', 'Western Asia'),
('Turkey', 'Republic of Turkey', 'TR', 'TUR', 'Asia', 'Western Asia'),
('Russia', 'Russian Federation', 'RU', 'RUS', 'Europe', 'Eastern Europe'),
('Ukraine', 'Ukraine', 'UA', 'UKR', 'Europe', 'Eastern Europe'),
('Czech Republic', 'Czech Republic', 'CZ', 'CZE', 'Europe', 'Eastern Europe'),
('Romania', 'Romania', 'RO', 'ROU', 'Europe', 'Eastern Europe'),
('Greece', 'Hellenic Republic', 'GR', 'GRC', 'Europe', 'Southern Europe'),
('Thailand', 'Kingdom of Thailand', 'TH', 'THA', 'Asia', 'South-Eastern Asia'),
('Vietnam', 'Socialist Republic of Vietnam', 'VN', 'VNM', 'Asia', 'South-Eastern Asia'),
('Indonesia', 'Republic of Indonesia', 'ID', 'IDN', 'Asia', 'South-Eastern Asia'),
('Philippines', 'Republic of the Philippines', 'PH', 'PHL', 'Asia', 'South-Eastern Asia'),
('Malaysia', 'Malaysia', 'MY', 'MYS', 'Asia', 'South-Eastern Asia'),
('Pakistan', 'Islamic Republic of Pakistan', 'PK', 'PAK', 'Asia', 'Southern Asia'),
('Bangladesh', 'People''s Republic of Bangladesh', 'BD', 'BGD', 'Asia', 'Southern Asia'),
('Egypt', 'Arab Republic of Egypt', 'EG', 'EGY', 'Africa', 'Northern Africa'),
('Nigeria', 'Federal Republic of Nigeria', 'NG', 'NGA', 'Africa', 'Western Africa')
ON CONFLICT (common_name) DO NOTHING;

-- FUNÇÃO: Normalizar nome de país
CREATE OR REPLACE FUNCTION normalize_country_name(input_name TEXT)
RETURNS TEXT AS $$
DECLARE
    normalized_name TEXT;
BEGIN
    -- Retornar NULL se input for NULL ou vazio
    IF input_name IS NULL OR TRIM(input_name) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Tentar match exato (case insensitive)
    SELECT common_name INTO normalized_name
    FROM sofia.countries
    WHERE LOWER(common_name) = LOWER(TRIM(input_name))
       OR LOWER(official_name) = LOWER(TRIM(input_name))
       OR UPPER(iso_alpha2) = UPPER(TRIM(input_name))
       OR UPPER(iso_alpha3) = UPPER(TRIM(input_name))
    LIMIT 1;
    
    -- Se não encontrou, tentar match parcial
    IF normalized_name IS NULL THEN
        SELECT common_name INTO normalized_name
        FROM sofia.countries
        WHERE LOWER(common_name) LIKE '%' || LOWER(TRIM(input_name)) || '%'
           OR LOWER(official_name) LIKE '%' || LOWER(TRIM(input_name)) || '%'
        ORDER BY LENGTH(common_name) ASC
        LIMIT 1;
    END IF;
    
    RETURN COALESCE(normalized_name, input_name);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- FUNÇÃO: Obter ou criar país
CREATE OR REPLACE FUNCTION get_or_create_country(input_name TEXT)
RETURNS INTEGER AS $$
DECLARE
    country_id_result INTEGER;
    normalized TEXT;
BEGIN
    IF input_name IS NULL OR TRIM(input_name) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Normalizar nome
    normalized := normalize_country_name(input_name);
    
    -- Buscar ID
    SELECT id INTO country_id_result
    FROM sofia.countries
    WHERE common_name = normalized
    LIMIT 1;
    
    -- Se não encontrou, criar novo
    IF country_id_result IS NULL THEN
        INSERT INTO sofia.countries (common_name, official_name)
        VALUES (TRIM(input_name), TRIM(input_name))
        ON CONFLICT (common_name) DO NOTHING
        RETURNING id INTO country_id_result;
        
        -- Se ainda for NULL (conflito), buscar novamente
        IF country_id_result IS NULL THEN
            SELECT id INTO country_id_result
            FROM sofia.countries
            WHERE common_name = TRIM(input_name)
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN country_id_result;
END;
$$ LANGUAGE plpgsql;

-- FUNÇÃO: Obter ou criar estado
CREATE OR REPLACE FUNCTION get_or_create_state(state_name TEXT, country_id_param INTEGER)
RETURNS INTEGER AS $$
DECLARE
    state_id_result INTEGER;
BEGIN
    IF state_name IS NULL OR TRIM(state_name) = '' OR country_id_param IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Buscar estado existente
    SELECT id INTO state_id_result
    FROM sofia.states
    WHERE LOWER(name) = LOWER(TRIM(state_name))
      AND country_id = country_id_param
    LIMIT 1;
    
    -- Se não encontrou, criar novo
    IF state_id_result IS NULL THEN
        INSERT INTO sofia.states (name, country_id)
        VALUES (TRIM(state_name), country_id_param)
        ON CONFLICT (name, country_id) DO NOTHING
        RETURNING id INTO state_id_result;
        
        -- Se ainda for NULL (conflito), buscar novamente
        IF state_id_result IS NULL THEN
            SELECT id INTO state_id_result
            FROM sofia.states
            WHERE LOWER(name) = LOWER(TRIM(state_name))
              AND country_id = country_id_param
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN state_id_result;
END;
$$ LANGUAGE plpgsql;

-- FUNÇÃO: Obter ou criar cidade
CREATE OR REPLACE FUNCTION get_or_create_city(city_name TEXT, state_id_param INTEGER, country_id_param INTEGER)
RETURNS INTEGER AS $$
DECLARE
    city_id_result INTEGER;
BEGIN
    IF city_name IS NULL OR TRIM(city_name) = '' OR country_id_param IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Buscar cidade existente
    SELECT id INTO city_id_result
    FROM sofia.cities
    WHERE LOWER(name) = LOWER(TRIM(city_name))
      AND (state_id = state_id_param OR (state_id IS NULL AND state_id_param IS NULL))
      AND country_id = country_id_param
    LIMIT 1;
    
    -- Se não encontrou, criar nova
    IF city_id_result IS NULL THEN
        INSERT INTO sofia.cities (name, state_id, country_id)
        VALUES (TRIM(city_name), state_id_param, country_id_param)
        ON CONFLICT (name, state_id, country_id) DO NOTHING
        RETURNING id INTO city_id_result;
        
        -- Se ainda for NULL (conflito), buscar novamente
        IF city_id_result IS NULL THEN
            SELECT id INTO city_id_result
            FROM sofia.cities
            WHERE LOWER(name) = LOWER(TRIM(city_name))
              AND (state_id = state_id_param OR (state_id IS NULL AND state_id_param IS NULL))
              AND country_id = country_id_param
            LIMIT 1;
        END IF;
    END IF;
    
    RETURN city_id_result;
END;
$$ LANGUAGE plpgsql;

-- Verificar criação
SELECT 'Tabelas criadas:' AS status;
SELECT COUNT(*) AS total_countries FROM sofia.countries;
SELECT 'Funções criadas: normalize_country_name, get_or_create_country, get_or_create_state, get_or_create_city' AS functions;
