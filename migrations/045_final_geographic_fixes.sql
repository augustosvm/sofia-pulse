-- Final geographic fixes - complete normalization
DO $$
BEGIN
    -- sports_regional: use iso_alpha3 instead of iso_alpha2
    UPDATE sofia.sports_regional s
    SET country_id = c.id
    FROM sofia.countries c
    WHERE s.country_id IS NULL
    AND s.country_code IS NOT NULL
    AND UPPER(s.country_code) = c.iso_alpha3;

    -- persons: HK and TW special cases
    UPDATE sofia.persons SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'HK') WHERE country = 'HK' AND country_id IS NULL;
    UPDATE sofia.persons SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'TW') WHERE country = 'TW' AND country_id IS NULL;

    -- comexstat_trade: Portuguese names
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'United States') WHERE country_name = 'Estados Unidos' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Mexico') WHERE country_name = 'México' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Germany') WHERE country_name = 'Alemanha' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'United Kingdom') WHERE country_name = 'Reino Unido' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'South Korea') WHERE country_name = 'Coreia do Sul' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Italy') WHERE country_name = 'Itália' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Vietnam') WHERE country_name = 'Vietnã' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Panama') WHERE country_name = 'Panamá' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'TW') WHERE country_name = 'Taiwan (Formosa)' AND country_id IS NULL;
    UPDATE sofia.comexstat_trade SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'HK') WHERE country_name = 'Hong Kong' AND country_id IS NULL;

    -- tech_jobs: Brazilian states to Brazil
    UPDATE sofia.tech_jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BR')
    WHERE country_id IS NULL AND country IN ('Ceará', 'Minas Gerais', 'Distrito Federal', 'São Paulo', 'Rio de Janeiro', 'Bahia', 'Paraná', 'Rio Grande do Sul');

    -- tech_jobs: handle provinces/states
    UPDATE sofia.tech_jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CA') WHERE country = 'British Columbia' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL') WHERE country = 'Noord-Brabant' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'GB') WHERE country = 'Berkshire' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AU') WHERE country = 'Australian Capital Territory' AND country_id IS NULL;

    -- jobs: handle common patterns
    UPDATE sofia.jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US') WHERE country IN ('NY • United States', 'Saint Louis County') AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CA') WHERE country = 'Greater Vancouver' AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AU') WHERE country IN ('The Rocks', 'Middle Park') AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US') WHERE country = 'Robertson' AND country_id IS NULL;

    RAISE NOTICE '✅ Final fixes applied';
END $$;
