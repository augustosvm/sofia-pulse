-- Adicionar TODOS os 195 países reconhecidos pela ONU
-- Isso evita usar Google Maps API para normalizar países (economia de custos)

INSERT INTO sofia.countries (common_name, official_name, iso_alpha2, iso_alpha3, region, subregion) VALUES
-- Países que faltam (145 adicionais aos 50 já existentes)
('Afghanistan', 'Islamic Republic of Afghanistan', 'AF', 'AFG', 'Asia', 'Southern Asia'),
('Albania', 'Republic of Albania', 'AL', 'ALB', 'Europe', 'Southern Europe'),
('Algeria', 'People''s Democratic Republic of Algeria', 'DZ', 'DZA', 'Africa', 'Northern Africa'),
('Andorra', 'Principality of Andorra', 'AD', 'AND', 'Europe', 'Southern Europe'),
('Angola', 'Republic of Angola', 'AO', 'AGO', 'Africa', 'Middle Africa'),
('Antigua and Barbuda', 'Antigua and Barbuda', 'AG', 'ATG', 'Americas', 'Caribbean'),
('Armenia', 'Republic of Armenia', 'AM', 'ARM', 'Asia', 'Western Asia'),
('Azerbaijan', 'Republic of Azerbaijan', 'AZ', 'AZE', 'Asia', 'Western Asia'),
('Bahamas', 'Commonwealth of the Bahamas', 'BS', 'BHS', 'Americas', 'Caribbean'),
('Bahrain', 'Kingdom of Bahrain', 'BH', 'BHR', 'Asia', 'Western Asia'),
('Barbados', 'Barbados', 'BB', 'BRB', 'Americas', 'Caribbean'),
('Belarus', 'Republic of Belarus', 'BY', 'BLR', 'Europe', 'Eastern Europe'),
('Belize', 'Belize', 'BZ', 'BLZ', 'Americas', 'Central America'),
('Benin', 'Republic of Benin', 'BJ', 'BEN', 'Africa', 'Western Africa'),
('Bhutan', 'Kingdom of Bhutan', 'BT', 'BTN', 'Asia', 'Southern Asia'),
('Bolivia', 'Plurinational State of Bolivia', 'BO', 'BOL', 'Americas', 'South America'),
('Bosnia and Herzegovina', 'Bosnia and Herzegovina', 'BA', 'BIH', 'Europe', 'Southern Europe'),
('Botswana', 'Republic of Botswana', 'BW', 'BWA', 'Africa', 'Southern Africa'),
('Brunei', 'Nation of Brunei', 'BN', 'BRN', 'Asia', 'South-Eastern Asia'),
('Bulgaria', 'Republic of Bulgaria', 'BG', 'BGR', 'Europe', 'Eastern Europe'),
('Burkina Faso', 'Burkina Faso', 'BF', 'BFA', 'Africa', 'Western Africa'),
('Burundi', 'Republic of Burundi', 'BI', 'BDI', 'Africa', 'Eastern Africa'),
('Cambodia', 'Kingdom of Cambodia', 'KH', 'KHM', 'Asia', 'South-Eastern Asia'),
('Cameroon', 'Republic of Cameroon', 'CM', 'CMR', 'Africa', 'Middle Africa'),
('Cape Verde', 'Republic of Cabo Verde', 'CV', 'CPV', 'Africa', 'Western Africa'),
('Central African Republic', 'Central African Republic', 'CF', 'CAF', 'Africa', 'Middle Africa'),
('Chad', 'Republic of Chad', 'TD', 'TCD', 'Africa', 'Middle Africa'),
('Comoros', 'Union of the Comoros', 'KM', 'COM', 'Africa', 'Eastern Africa'),
('Congo', 'Republic of the Congo', 'CG', 'COG', 'Africa', 'Middle Africa'),
('Costa Rica', 'Republic of Costa Rica', 'CR', 'CRI', 'Americas', 'Central America'),
('Croatia', 'Republic of Croatia', 'HR', 'HRV', 'Europe', 'Southern Europe'),
('Cuba', 'Republic of Cuba', 'CU', 'CUB', 'Americas', 'Caribbean'),
('Cyprus', 'Republic of Cyprus', 'CY', 'CYP', 'Asia', 'Western Asia'),
('Democratic Republic of the Congo', 'Democratic Republic of the Congo', 'CD', 'COD', 'Africa', 'Middle Africa'),
('Djibouti', 'Republic of Djibouti', 'DJ', 'DJI', 'Africa', 'Eastern Africa'),
('Dominica', 'Commonwealth of Dominica', 'DM', 'DMA', 'Americas', 'Caribbean'),
('Dominican Republic', 'Dominican Republic', 'DO', 'DOM', 'Americas', 'Caribbean'),
('Ecuador', 'Republic of Ecuador', 'EC', 'ECU', 'Americas', 'South America'),
('El Salvador', 'Republic of El Salvador', 'SV', 'SLV', 'Americas', 'Central America'),
('Equatorial Guinea', 'Republic of Equatorial Guinea', 'GQ', 'GNQ', 'Africa', 'Middle Africa'),
('Eritrea', 'State of Eritrea', 'ER', 'ERI', 'Africa', 'Eastern Africa'),
('Estonia', 'Republic of Estonia', 'EE', 'EST', 'Europe', 'Northern Europe'),
('Eswatini', 'Kingdom of Eswatini', 'SZ', 'SWZ', 'Africa', 'Southern Africa'),
('Ethiopia', 'Federal Democratic Republic of Ethiopia', 'ET', 'ETH', 'Africa', 'Eastern Africa'),
('Fiji', 'Republic of Fiji', 'FJ', 'FJI', 'Oceania', 'Melanesia'),
('Gabon', 'Gabonese Republic', 'GA', 'GAB', 'Africa', 'Middle Africa'),
('Gambia', 'Republic of the Gambia', 'GM', 'GMB', 'Africa', 'Western Africa'),
('Georgia', 'Georgia', 'GE', 'GEO', 'Asia', 'Western Asia'),
('Ghana', 'Republic of Ghana', 'GH', 'GHA', 'Africa', 'Western Africa'),
('Grenada', 'Grenada', 'GD', 'GRD', 'Americas', 'Caribbean'),
('Guatemala', 'Republic of Guatemala', 'GT', 'GTM', 'Americas', 'Central America'),
('Guinea', 'Republic of Guinea', 'GN', 'GIN', 'Africa', 'Western Africa'),
('Guinea-Bissau', 'Republic of Guinea-Bissau', 'GW', 'GNB', 'Africa', 'Western Africa'),
('Guyana', 'Co-operative Republic of Guyana', 'GY', 'GUY', 'Americas', 'South America'),
('Haiti', 'Republic of Haiti', 'HT', 'HTI', 'Americas', 'Caribbean'),
('Honduras', 'Republic of Honduras', 'HN', 'HND', 'Americas', 'Central America'),
('Hungary', 'Hungary', 'HU', 'HUN', 'Europe', 'Eastern Europe'),
('Iceland', 'Iceland', 'IS', 'ISL', 'Europe', 'Northern Europe'),
('Iran', 'Islamic Republic of Iran', 'IR', 'IRN', 'Asia', 'Southern Asia'),
('Iraq', 'Republic of Iraq', 'IQ', 'IRQ', 'Asia', 'Western Asia'),
('Ivory Coast', 'Republic of Côte d''Ivoire', 'CI', 'CIV', 'Africa', 'Western Africa'),
('Jamaica', 'Jamaica', 'JM', 'JAM', 'Americas', 'Caribbean'),
('Jordan', 'Hashemite Kingdom of Jordan', 'JO', 'JOR', 'Asia', 'Western Asia'),
('Kazakhstan', 'Republic of Kazakhstan', 'KZ', 'KAZ', 'Asia', 'Central Asia'),
('Kenya', 'Republic of Kenya', 'KE', 'KEN', 'Africa', 'Eastern Africa'),
('Kiribati', 'Republic of Kiribati', 'KI', 'KIR', 'Oceania', 'Micronesia'),
('Kuwait', 'State of Kuwait', 'KW', 'KWT', 'Asia', 'Western Asia'),
('Kyrgyzstan', 'Kyrgyz Republic', 'KG', 'KGZ', 'Asia', 'Central Asia'),
('Laos', 'Lao People''s Democratic Republic', 'LA', 'LAO', 'Asia', 'South-Eastern Asia'),
('Latvia', 'Republic of Latvia', 'LV', 'LVA', 'Europe', 'Northern Europe'),
('Lebanon', 'Lebanese Republic', 'LB', 'LBN', 'Asia', 'Western Asia'),
('Lesotho', 'Kingdom of Lesotho', 'LS', 'LSO', 'Africa', 'Southern Africa'),
('Liberia', 'Republic of Liberia', 'LR', 'LBR', 'Africa', 'Western Africa'),
('Libya', 'State of Libya', 'LY', 'LBY', 'Africa', 'Northern Africa'),
('Liechtenstein', 'Principality of Liechtenstein', 'LI', 'LIE', 'Europe', 'Western Europe'),
('Lithuania', 'Republic of Lithuania', 'LT', 'LTU', 'Europe', 'Northern Europe'),
('Luxembourg', 'Grand Duchy of Luxembourg', 'LU', 'LUX', 'Europe', 'Western Europe'),
('Madagascar', 'Republic of Madagascar', 'MG', 'MDG', 'Africa', 'Eastern Africa'),
('Malawi', 'Republic of Malawi', 'MW', 'MWI', 'Africa', 'Eastern Africa'),
('Maldives', 'Republic of Maldives', 'MV', 'MDV', 'Asia', 'Southern Asia'),
('Mali', 'Republic of Mali', 'ML', 'MLI', 'Africa', 'Western Africa'),
('Malta', 'Republic of Malta', 'MT', 'MLT', 'Europe', 'Southern Europe'),
('Marshall Islands', 'Republic of the Marshall Islands', 'MH', 'MHL', 'Oceania', 'Micronesia'),
('Mauritania', 'Islamic Republic of Mauritania', 'MR', 'MRT', 'Africa', 'Western Africa'),
('Mauritius', 'Republic of Mauritius', 'MU', 'MUS', 'Africa', 'Eastern Africa'),
('Micronesia', 'Federated States of Micronesia', 'FM', 'FSM', 'Oceania', 'Micronesia'),
('Moldova', 'Republic of Moldova', 'MD', 'MDA', 'Europe', 'Eastern Europe'),
('Monaco', 'Principality of Monaco', 'MC', 'MCO', 'Europe', 'Western Europe'),
('Mongolia', 'Mongolia', 'MN', 'MNG', 'Asia', 'Eastern Asia'),
('Montenegro', 'Montenegro', 'ME', 'MNE', 'Europe', 'Southern Europe'),
('Morocco', 'Kingdom of Morocco', 'MA', 'MAR', 'Africa', 'Northern Africa'),
('Mozambique', 'Republic of Mozambique', 'MZ', 'MOZ', 'Africa', 'Eastern Africa'),
('Myanmar', 'Republic of the Union of Myanmar', 'MM', 'MMR', 'Asia', 'South-Eastern Asia'),
('Namibia', 'Republic of Namibia', 'NA', 'NAM', 'Africa', 'Southern Africa'),
('Nauru', 'Republic of Nauru', 'NR', 'NRU', 'Oceania', 'Micronesia'),
('Nepal', 'Federal Democratic Republic of Nepal', 'NP', 'NPL', 'Asia', 'Southern Asia'),
('Nicaragua', 'Republic of Nicaragua', 'NI', 'NIC', 'Americas', 'Central America'),
('Niger', 'Republic of Niger', 'NE', 'NER', 'Africa', 'Western Africa'),
('North Korea', 'Democratic People''s Republic of Korea', 'KP', 'PRK', 'Asia', 'Eastern Asia'),
('North Macedonia', 'Republic of North Macedonia', 'MK', 'MKD', 'Europe', 'Southern Europe'),
('Oman', 'Sultanate of Oman', 'OM', 'OMN', 'Asia', 'Western Asia'),
('Palau', 'Republic of Palau', 'PW', 'PLW', 'Oceania', 'Micronesia'),
('Palestine', 'State of Palestine', 'PS', 'PSE', 'Asia', 'Western Asia'),
('Panama', 'Republic of Panama', 'PA', 'PAN', 'Americas', 'Central America'),
('Papua New Guinea', 'Independent State of Papua New Guinea', 'PG', 'PNG', 'Oceania', 'Melanesia'),
('Paraguay', 'Republic of Paraguay', 'PY', 'PRY', 'Americas', 'South America'),
('Qatar', 'State of Qatar', 'QA', 'QAT', 'Asia', 'Western Asia'),
('Rwanda', 'Republic of Rwanda', 'RW', 'RWA', 'Africa', 'Eastern Africa'),
('Saint Kitts and Nevis', 'Federation of Saint Christopher and Nevis', 'KN', 'KNA', 'Americas', 'Caribbean'),
('Saint Lucia', 'Saint Lucia', 'LC', 'LCA', 'Americas', 'Caribbean'),
('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines', 'VC', 'VCT', 'Americas', 'Caribbean'),
('Samoa', 'Independent State of Samoa', 'WS', 'WSM', 'Oceania', 'Polynesia'),
('San Marino', 'Republic of San Marino', 'SM', 'SMR', 'Europe', 'Southern Europe'),
('Sao Tome and Principe', 'Democratic Republic of São Tomé and Príncipe', 'ST', 'STP', 'Africa', 'Middle Africa'),
('Senegal', 'Republic of Senegal', 'SN', 'SEN', 'Africa', 'Western Africa'),
('Serbia', 'Republic of Serbia', 'RS', 'SRB', 'Europe', 'Southern Europe'),
('Seychelles', 'Republic of Seychelles', 'SC', 'SYC', 'Africa', 'Eastern Africa'),
('Sierra Leone', 'Republic of Sierra Leone', 'SL', 'SLE', 'Africa', 'Western Africa'),
('Slovakia', 'Slovak Republic', 'SK', 'SVK', 'Europe', 'Eastern Europe'),
('Slovenia', 'Republic of Slovenia', 'SI', 'SVN', 'Europe', 'Southern Europe'),
('Solomon Islands', 'Solomon Islands', 'SB', 'SLB', 'Oceania', 'Melanesia'),
('Somalia', 'Federal Republic of Somalia', 'SO', 'SOM', 'Africa', 'Eastern Africa'),
('South Sudan', 'Republic of South Sudan', 'SS', 'SSD', 'Africa', 'Eastern Africa'),
('Sri Lanka', 'Democratic Socialist Republic of Sri Lanka', 'LK', 'LKA', 'Asia', 'Southern Asia'),
('Sudan', 'Republic of the Sudan', 'SD', 'SDN', 'Africa', 'Northern Africa'),
('Suriname', 'Republic of Suriname', 'SR', 'SUR', 'Americas', 'South America'),
('Syria', 'Syrian Arab Republic', 'SY', 'SYR', 'Asia', 'Western Asia'),
('Tajikistan', 'Republic of Tajikistan', 'TJ', 'TJK', 'Asia', 'Central Asia'),
('Tanzania', 'United Republic of Tanzania', 'TZ', 'TZA', 'Africa', 'Eastern Africa'),
('Timor-Leste', 'Democratic Republic of Timor-Leste', 'TL', 'TLS', 'Asia', 'South-Eastern Asia'),
('Togo', 'Togolese Republic', 'TG', 'TGO', 'Africa', 'Western Africa'),
('Tonga', 'Kingdom of Tonga', 'TO', 'TON', 'Oceania', 'Polynesia'),
('Trinidad and Tobago', 'Republic of Trinidad and Tobago', 'TT', 'TTO', 'Americas', 'Caribbean'),
('Tunisia', 'Republic of Tunisia', 'TN', 'TUN', 'Africa', 'Northern Africa'),
('Turkmenistan', 'Turkmenistan', 'TM', 'TKM', 'Asia', 'Central Asia'),
('Tuvalu', 'Tuvalu', 'TV', 'TUV', 'Oceania', 'Polynesia'),
('Uganda', 'Republic of Uganda', 'UG', 'UGA', 'Africa', 'Eastern Africa'),
('Uruguay', 'Oriental Republic of Uruguay', 'UY', 'URY', 'Americas', 'South America'),
('Uzbekistan', 'Republic of Uzbekistan', 'UZ', 'UZB', 'Asia', 'Central Asia'),
('Vanuatu', 'Republic of Vanuatu', 'VU', 'VUT', 'Oceania', 'Melanesia'),
('Vatican City', 'Vatican City State', 'VA', 'VAT', 'Europe', 'Southern Europe'),
('Venezuela', 'Bolivarian Republic of Venezuela', 'VE', 'VEN', 'Americas', 'South America'),
('Yemen', 'Republic of Yemen', 'YE', 'YEM', 'Asia', 'Western Asia'),
('Zambia', 'Republic of Zambia', 'ZM', 'ZMB', 'Africa', 'Eastern Africa'),
('Zimbabwe', 'Republic of Zimbabwe', 'ZW', 'ZWE', 'Africa', 'Eastern Africa')
ON CONFLICT (common_name) DO NOTHING;

-- Remigrar todas as tabelas com lista completa
UPDATE sofia.jobs
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

UPDATE sofia.nih_grants
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

UPDATE sofia.funding_rounds
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

UPDATE sofia.tech_jobs
SET country_id = get_or_create_country(country)
WHERE country IS NOT NULL AND country_id IS NULL;

-- Relatório
SELECT 'COUNTRIES EXPANDED' AS status, COUNT(*)::TEXT || ' countries' AS result FROM sofia.countries;

SELECT 
    'jobs' AS table_name, 
    COUNT(*) AS total, 
    COUNT(country_id) AS with_country,
    ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2) AS pct
FROM sofia.jobs
UNION ALL
SELECT 'tech_jobs', COUNT(*), COUNT(country_id), ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.tech_jobs
UNION ALL
SELECT 'funding_rounds', COUNT(*), COUNT(country_id), ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.funding_rounds
UNION ALL
SELECT 'nih_grants', COUNT(*), COUNT(country_id), ROUND(100.0 * COUNT(country_id) / NULLIF(COUNT(*), 0), 2)
FROM sofia.nih_grants
ORDER BY total DESC;
