-- Comprehensive geographic mapping - all remaining cases
DO $$
DECLARE
    us_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'US');
    br_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BR');
    au_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AU');
    nz_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NZ');
    za_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'ZA');
    de_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'DE');
    at_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'AT');
    nl_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'NL');
    ie_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'IE');
    ch_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'CH');
    fr_id INT := (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'FR');
BEGIN
    -- comexstat_trade: Portuguese names
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Denmark') WHERE c.country_name = 'Dinamarca' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Spain') WHERE c.country_name = 'Espanha' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Paraguay') WHERE c.country_name = 'Paraguai' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Norway') WHERE c.country_name = 'Noruega' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Sweden') WHERE c.country_name = 'Suécia' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Canada') WHERE c.country_name = 'Canadá' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'France') WHERE c.country_name = 'França' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE common_name = 'Australia') WHERE c.country_name = 'Austrália' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'TW') WHERE c.country_name LIKE 'Taiwan%' AND c.country_id IS NULL;
    UPDATE sofia.comexstat_trade c SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'HK') WHERE c.country_name LIKE 'Hong Kong%' AND c.country_id IS NULL;

    -- tech_jobs: states/regions
    UPDATE sofia.tech_jobs SET country_id = br_id WHERE country IN ('Pernambuco', 'Bahia', 'Santa Catarina', 'Goiás', 'Paraíba') AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = de_id WHERE country IN ('Pinneberg (Kreis)', 'Region Hannover (Kreis)', 'Bayern', 'Baden-Württemberg') AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = at_id WHERE country = 'Österreich' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = nl_id WHERE country = 'Nederland' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = ie_id WHERE country LIKE 'Dublin%' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = us_id WHERE country IN ('Saint Louis County', 'Fairfax County', 'US-SF', 'US-NYC', 'US-SEA') AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = au_id WHERE country LIKE '%Brisbane%' AND country_id IS NULL;
    UPDATE sofia.tech_jobs SET country_id = nz_id WHERE country LIKE '%Auckland%' AND country_id IS NULL;

    -- jobs: regions/states
    UPDATE sofia.jobs SET country_id = za_id WHERE country IN ('Gauteng', 'Tshwane', 'Western Cape') AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = nz_id WHERE country IN ('North Island', 'Auckland') AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = us_id WHERE country IN ('Kinloch', 'Fairfax County', 'US-SF', 'US-NYC') AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = ch_id WHERE country = 'Bern-Mittelland' AND country_id IS NULL;
    UPDATE sofia.jobs SET country_id = fr_id WHERE country = 'Haute-Garonne' AND country_id IS NULL;

    RAISE NOTICE '✅ Comprehensive mappings applied';
END $$;
