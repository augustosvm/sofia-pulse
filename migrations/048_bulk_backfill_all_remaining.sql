-- Bulk backfill all remaining tables
DO $$
BEGIN
    RAISE NOTICE '🚀 Backfilling all remaining tables...';

    -- ========================================================================
    -- ORGANIZATIONS
    -- ========================================================================

    -- market_data_brazil
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT company, LOWER(TRIM(REGEXP_REPLACE(company, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'market_data_brazil'), 'company'
    FROM sofia.market_data_brazil WHERE company IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.market_data_brazil m SET organization_id = o.id
    FROM sofia.organizations o
    WHERE m.organization_id IS NULL AND m.company IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(m.company, '[^a-zA-Z0-9\s]', '', 'g')));

    -- market_data_nasdaq
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT company, LOWER(TRIM(REGEXP_REPLACE(company, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'market_data_nasdaq'), 'company'
    FROM sofia.market_data_nasdaq WHERE company IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.market_data_nasdaq m SET organization_id = o.id
    FROM sofia.organizations o
    WHERE m.organization_id IS NULL AND m.company IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(m.company, '[^a-zA-Z0-9\s]', '', 'g')));

    -- global_universities_progress
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT institution_name, LOWER(TRIM(REGEXP_REPLACE(institution_name, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'global_universities_progress', 'institution_id', institution_id), 'university'
    FROM sofia.global_universities_progress WHERE institution_name IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.global_universities_progress g SET organization_id = o.id
    FROM sofia.organizations o
    WHERE g.organization_id IS NULL AND g.institution_name IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(g.institution_name, '[^a-zA-Z0-9\s]', '', 'g')));

    -- world_ngos
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT name, LOWER(TRIM(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'world_ngos', 'headquarters', headquarters_country), 'ngo'
    FROM sofia.world_ngos WHERE name IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.world_ngos w SET organization_id = o.id
    FROM sofia.organizations o
    WHERE w.organization_id IS NULL AND w.name IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(w.name, '[^a-zA-Z0-9\s]', '', 'g')));

    -- hdx_humanitarian_data
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT organization, LOWER(TRIM(REGEXP_REPLACE(organization, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'hdx_humanitarian_data'), 'ngo'
    FROM sofia.hdx_humanitarian_data WHERE organization IS NOT NULL AND organization != ''
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.hdx_humanitarian_data h SET organization_id = o.id
    FROM sofia.organizations o
    WHERE h.organization_id IS NULL AND h.organization IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(h.organization, '[^a-zA-Z0-9\s]', '', 'g')));

    -- hkex_ipos
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT company, LOWER(TRIM(REGEXP_REPLACE(company, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'hkex_ipos', 'company_cn', company_cn), 'company'
    FROM sofia.hkex_ipos WHERE company IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.hkex_ipos h SET organization_id = o.id
    FROM sofia.organizations o
    WHERE h.organization_id IS NULL AND h.company IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(h.company, '[^a-zA-Z0-9\s]', '', 'g')));

    -- startups
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT name, LOWER(TRIM(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'startups'), 'startup'
    FROM sofia.startups WHERE name IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.startups s SET organization_id = o.id
    FROM sofia.organizations o
    WHERE s.organization_id IS NULL AND s.name IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(s.name, '[^a-zA-Z0-9\s]', '', 'g')));

    -- nih_grants
    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT organization, LOWER(TRIM(REGEXP_REPLACE(organization, '[^a-zA-Z0-9\s]', '', 'g'))),
           jsonb_build_object('source', 'nih_grants'), 'university'
    FROM sofia.nih_grants WHERE organization IS NOT NULL
    ON CONFLICT (normalized_name) DO NOTHING;

    UPDATE sofia.nih_grants n SET organization_id = o.id
    FROM sofia.organizations o
    WHERE n.organization_id IS NULL AND n.organization IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(n.organization, '[^a-zA-Z0-9\s]', '', 'g')));

    RAISE NOTICE '✅ Organizations backfilled';

    -- ========================================================================
    -- GEOGRAPHIC
    -- ========================================================================

    -- authors (primary_country)
    UPDATE sofia.authors a SET country_id = c.id
    FROM sofia.countries c
    WHERE a.country_id IS NULL AND a.primary_country IS NOT NULL
    AND (UPPER(a.primary_country) = c.iso_alpha2 OR UPPER(a.primary_country) = c.iso_alpha3 OR LOWER(TRIM(a.primary_country)) = LOWER(c.common_name));

    -- publications (institution_country)
    UPDATE sofia.publications p SET country_id = c.id
    FROM sofia.countries c
    WHERE p.country_id IS NULL AND p.institution_country IS NOT NULL
    AND (UPPER(p.institution_country) = c.iso_alpha2 OR UPPER(p.institution_country) = c.iso_alpha3 OR LOWER(TRIM(p.institution_country)) = LOWER(c.common_name));

    -- gdelt_events (action_geo_country)
    UPDATE sofia.gdelt_events g SET country_id = c.id
    FROM sofia.countries c
    WHERE g.country_id IS NULL AND g.action_geo_country IS NOT NULL
    AND (UPPER(g.action_geo_country) = c.iso_alpha2 OR UPPER(g.action_geo_country) = c.iso_alpha3 OR LOWER(TRIM(g.action_geo_country)) = LOWER(c.common_name));

    -- cardboard_production
    UPDATE sofia.cardboard_production cp SET country_id = c.id
    FROM sofia.countries c
    WHERE cp.country_id IS NULL AND cp.country IS NOT NULL
    AND (UPPER(cp.country) = c.iso_alpha2 OR UPPER(cp.country) = c.iso_alpha3 OR LOWER(TRIM(cp.country)) = LOWER(c.common_name));

    -- electricity_consumption
    UPDATE sofia.electricity_consumption ec SET country_id = c.id
    FROM sofia.countries c
    WHERE ec.country_id IS NULL AND ec.country IS NOT NULL
    AND (UPPER(ec.country) = c.iso_alpha2 OR UPPER(ec.country) = c.iso_alpha3 OR LOWER(TRIM(ec.country)) = LOWER(c.common_name));

    -- energy_global
    UPDATE sofia.energy_global eg SET country_id = c.id
    FROM sofia.countries c
    WHERE eg.country_id IS NULL AND eg.country IS NOT NULL
    AND (UPPER(eg.country) = c.iso_alpha2 OR UPPER(eg.country) = c.iso_alpha3 OR LOWER(TRIM(eg.country)) = LOWER(c.common_name));

    -- gender_names
    UPDATE sofia.gender_names gn SET country_id = c.id
    FROM sofia.countries c
    WHERE gn.country_id IS NULL AND gn.country_code IS NOT NULL
    AND (UPPER(gn.country_code) = c.iso_alpha2 OR UPPER(gn.country_code) = c.iso_alpha3);

    -- global_universities_progress (country_code)
    UPDATE sofia.global_universities_progress g SET country_id = c.id
    FROM sofia.countries c
    WHERE g.country_id IS NULL AND g.country_code IS NOT NULL
    AND (UPPER(g.country_code) = c.iso_alpha2 OR UPPER(g.country_code) = c.iso_alpha3);

    -- world_ngos (headquarters_country)
    UPDATE sofia.world_ngos w SET country_id = c.id
    FROM sofia.countries c
    WHERE w.country_id IS NULL AND w.headquarters_country IS NOT NULL
    AND (UPPER(w.headquarters_country) = c.iso_alpha2 OR UPPER(w.headquarters_country) = c.iso_alpha3 OR LOWER(TRIM(w.headquarters_country)) = LOWER(c.common_name));

    -- startups
    UPDATE sofia.startups s SET country_id = c.id
    FROM sofia.countries c
    WHERE s.country_id IS NULL AND s.country IS NOT NULL
    AND (UPPER(s.country) = c.iso_alpha2 OR UPPER(s.country) = c.iso_alpha3 OR LOWER(TRIM(s.country)) = LOWER(c.common_name));

    RAISE NOTICE '✅ Geographic backfilled';
    RAISE NOTICE '✅ All remaining tables normalized!';

END $$;
