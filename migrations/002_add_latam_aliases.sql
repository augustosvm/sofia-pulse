-- Adicionar aliases LATAM faltantes em dim_country_alias

INSERT INTO sofia.dim_country_alias (country_code_iso2, alias_text, source) VALUES
-- América Central
('HN', 'Honduras', 'ACLED'),
('GT', 'Guatemala', 'ACLED'),
('HT', 'Haiti', 'ACLED'),
('SV', 'El Salvador', 'ACLED'),
('TT', 'Trinidad and Tobago', 'ACLED'),
('JM', 'Jamaica', 'ACLED'),
('PR', 'Puerto Rico', 'ACLED'),
('PA', 'Panama', 'ACLED'),
('NI', 'Nicaragua', 'ACLED'),
('CR', 'Costa Rica', 'ACLED'),
('DO', 'Dominican Republic', 'ACLED'),
('CU', 'Cuba', 'ACLED'),
('BZ', 'Belize', 'ACLED'),

-- América do Sul (verificar se já existem)
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
('GY', 'Guyana', 'ACLED'),
('SR', 'Suriname', 'ACLED'),
('GF', 'French Guiana', 'ACLED'),

-- Caribe
('BS', 'Bahamas', 'ACLED'),
('BB', 'Barbados', 'ACLED'),
('GD', 'Grenada', 'ACLED'),
('LC', 'Saint Lucia', 'ACLED'),
('VC', 'Saint Vincent and the Grenadines', 'ACLED'),
('AG', 'Antigua and Barbuda', 'ACLED'),
('DM', 'Dominica', 'ACLED'),
('KN', 'Saint Kitts and Nevis', 'ACLED')

ON CONFLICT (alias_text, source) DO NOTHING;
