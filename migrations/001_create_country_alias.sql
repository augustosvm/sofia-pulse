-- ============================================================================
-- ACLED Pipeline Fix: Country Alias Mapping
-- ============================================================================
-- Cria tabela de aliases para resolver nomes de países de múltiplas fontes

CREATE TABLE IF NOT EXISTS sofia.dim_country_alias (
    country_code_iso2 VARCHAR(2) NOT NULL,
    alias_text VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (alias_text, source),
    FOREIGN KEY (country_code_iso2) REFERENCES sofia.dim_country(country_code_iso2)
);

CREATE INDEX IF NOT EXISTS idx_country_alias_lookup 
ON sofia.dim_country_alias(LOWER(alias_text));

-- Popula aliases essenciais para ACLED (nomes que diferem de country_name_en)
INSERT INTO sofia.dim_country_alias (country_code_iso2, alias_text, source) VALUES
-- América Latina
('BR', 'Brazil', 'ACLED'),
('AR', 'Argentina', 'ACLED'),
('CL', 'Chile', 'ACLED'),
('CO', 'Colombia', 'ACLED'),
('PE', 'Peru', 'ACLED'),
('VE', 'Venezuela', 'ACLED'),
('BO', 'Bolivia', 'ACLED'),
('EC', 'Ecuador', 'ACLED'),
('PY', 'Paraguay', 'ACLED'),
('UY', 'Uruguay', 'ACLED'),
('MX', 'Mexico', 'ACLED'),
('GT', 'Guatemala', 'ACLED'),
('HN', 'Honduras', 'ACLED'),
('SV', 'El Salvador', 'ACLED'),
('NI', 'Nicaragua', 'ACLED'),
('CR', 'Costa Rica', 'ACLED'),
('PA', 'Panama', 'ACLED'),
('CU', 'Cuba', 'ACLED'),
('DO', 'Dominican Republic', 'ACLED'),
('HT', 'Haiti', 'ACLED'),
('JM', 'Jamaica', 'ACLED'),
('TT', 'Trinidad and Tobago', 'ACLED'),
('BS', 'Bahamas', 'ACLED'),
('BB', 'Barbados', 'ACLED'),
('GY', 'Guyana', 'ACLED'),
('SR', 'Suriname', 'ACLED'),
('BZ', 'Belize', 'ACLED'),

-- Casos problemáticos conhecidos
('MM', 'Myanmar (Burma)', 'ACLED'),
('MM', 'Burma', 'ACLED'),
('CD', 'Democratic Republic of Congo', 'ACLED'),
('CD', 'DR Congo', 'ACLED'),
('CG', 'Republic of Congo', 'ACLED'),
('CI', 'Ivory Coast', 'ACLED'),
('CI', 'Côte d''Ivoire', 'ACLED'),
('KP', 'North Korea', 'ACLED'),
('KR', 'South Korea', 'ACLED'),
('LA', 'Laos', 'ACLED'),
('SY', 'Syria', 'ACLED'),
('TZ', 'Tanzania', 'ACLED'),
('VN', 'Vietnam', 'ACLED'),
('PS', 'Palestine', 'ACLED'),
('PS', 'West Bank', 'ACLED'),
('PS', 'Gaza Strip', 'ACLED'),

-- Europa
('BA', 'Bosnia and Herzegovina', 'ACLED'),
('MK', 'North Macedonia', 'ACLED'),
('MD', 'Moldova', 'ACLED'),
('XK', 'Kosovo', 'ACLED'),

-- Outros
('US', 'United States', 'ACLED'),
('GB', 'United Kingdom', 'ACLED'),
('RU', 'Russia', 'ACLED')

ON CONFLICT (alias_text, source) DO NOTHING;

-- Adiciona também os nomes oficiais de dim_country como aliases
INSERT INTO sofia.dim_country_alias (country_code_iso2, alias_text, source)
SELECT country_code_iso2, country_name_en, 'dim_country'
FROM sofia.dim_country
WHERE country_name_en IS NOT NULL
ON CONFLICT (alias_text, source) DO NOTHING;

-- Adiciona nomes locais como aliases
INSERT INTO sofia.dim_country_alias (country_code_iso2, alias_text, source)
SELECT country_code_iso2, country_name_local, 'dim_country_local'
FROM sofia.dim_country
WHERE country_name_local IS NOT NULL 
  AND country_name_local != country_name_en
ON CONFLICT (alias_text, source) DO NOTHING;
