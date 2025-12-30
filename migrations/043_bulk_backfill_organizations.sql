-- ============================================================================
-- Migration 043: Bulk Backfill Organizations (FAST)
-- ============================================================================
-- Uses pure SQL bulk operations instead of row-by-row processing
-- Expected time: <1 minute vs 10+ hours
-- ============================================================================

DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_funding_inserted INT;
    v_space_inserted INT;
    v_tech_inserted INT;
    v_funding_linked INT;
    v_space_linked INT;
    v_tech_linked INT;
BEGIN
    v_start_time := clock_timestamp();
    RAISE NOTICE '🚀 Starting bulk organization backfill...';
    RAISE NOTICE '';

    -- ========================================================================
    -- STEP 1: Bulk insert organizations from funding_rounds
    -- ========================================================================
    RAISE NOTICE '1️⃣  FUNDING_ROUNDS → organizations';

    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT
        company_name,
        LOWER(TRIM(REGEXP_REPLACE(company_name, '[^a-zA-Z0-9\s]', '', 'g'))),
        jsonb_build_object(
            'source', 'funding_rounds',
            'city', city,
            'country', country
        ),
        'company'
    FROM sofia.funding_rounds
    WHERE company_name IS NOT NULL
    AND company_name != ''
    ON CONFLICT (normalized_name) DO NOTHING;

    GET DIAGNOSTICS v_funding_inserted = ROW_COUNT;
    RAISE NOTICE '   ✅ Inserted % new organizations', v_funding_inserted;

    -- Link funding_rounds to organizations
    UPDATE sofia.funding_rounds f
    SET organization_id = o.id
    FROM sofia.organizations o
    WHERE f.organization_id IS NULL
    AND f.company_name IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(f.company_name, '[^a-zA-Z0-9\s]', '', 'g')));

    GET DIAGNOSTICS v_funding_linked = ROW_COUNT;
    RAISE NOTICE '   🔗 Linked % funding rounds', v_funding_linked;
    RAISE NOTICE '';

    -- ========================================================================
    -- STEP 2: Bulk insert organizations from space_industry
    -- ========================================================================
    RAISE NOTICE '2️⃣  SPACE_INDUSTRY → organizations';

    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT
        company,
        LOWER(TRIM(REGEXP_REPLACE(company, '[^a-zA-Z0-9\s]', '', 'g'))),
        jsonb_build_object(
            'source', 'space_industry',
            'country', country,
            'industry', 'space'
        ),
        'company'
    FROM sofia.space_industry
    WHERE company IS NOT NULL
    AND company != ''
    ON CONFLICT (normalized_name) DO NOTHING;

    GET DIAGNOSTICS v_space_inserted = ROW_COUNT;
    RAISE NOTICE '   ✅ Inserted % new organizations', v_space_inserted;

    -- Link space_industry to organizations
    UPDATE sofia.space_industry s
    SET organization_id = o.id
    FROM sofia.organizations o
    WHERE s.organization_id IS NULL
    AND s.company IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(s.company, '[^a-zA-Z0-9\s]', '', 'g')));

    GET DIAGNOSTICS v_space_linked = ROW_COUNT;
    RAISE NOTICE '   🔗 Linked % space industry records', v_space_linked;
    RAISE NOTICE '';

    -- ========================================================================
    -- STEP 3: Bulk insert organizations from tech_jobs
    -- ========================================================================
    RAISE NOTICE '3️⃣  TECH_JOBS → organizations';

    INSERT INTO sofia.organizations (name, normalized_name, metadata, type)
    SELECT DISTINCT
        company,
        LOWER(TRIM(REGEXP_REPLACE(company, '[^a-zA-Z0-9\s]', '', 'g'))),
        jsonb_build_object(
            'source', 'tech_jobs',
            'url', company_url
        ),
        'employer'
    FROM sofia.tech_jobs
    WHERE company IS NOT NULL
    AND company != ''
    ON CONFLICT (normalized_name) DO NOTHING;

    GET DIAGNOSTICS v_tech_inserted = ROW_COUNT;
    RAISE NOTICE '   ✅ Inserted % new organizations', v_tech_inserted;

    -- Link tech_jobs to organizations
    UPDATE sofia.tech_jobs t
    SET organization_id = o.id
    FROM sofia.organizations o
    WHERE t.organization_id IS NULL
    AND t.company IS NOT NULL
    AND o.normalized_name = LOWER(TRIM(REGEXP_REPLACE(t.company, '[^a-zA-Z0-9\s]', '', 'g')));

    GET DIAGNOSTICS v_tech_linked = ROW_COUNT;
    RAISE NOTICE '   🔗 Linked % tech jobs', v_tech_linked;
    RAISE NOTICE '';

    -- ========================================================================
    -- SUMMARY
    -- ========================================================================
    RAISE NOTICE '📊 SUMMARY:';
    RAISE NOTICE '   Organizations inserted: % total',
        (v_funding_inserted + v_space_inserted + v_tech_inserted);
    RAISE NOTICE '   Records linked: % total',
        (v_funding_linked + v_space_linked + v_tech_linked);
    RAISE NOTICE '   Duration: %', (clock_timestamp() - v_start_time);
    RAISE NOTICE '';
    RAISE NOTICE '✅ Bulk backfill complete!';

END $$;

-- Show final coverage
DO $$
DECLARE
    v_funding_total INT;
    v_funding_linked INT;
    v_space_total INT;
    v_space_linked INT;
    v_tech_total INT;
    v_tech_linked INT;
BEGIN
    SELECT COUNT(*), COUNT(organization_id) INTO v_funding_total, v_funding_linked
    FROM sofia.funding_rounds WHERE company_name IS NOT NULL;

    SELECT COUNT(*), COUNT(organization_id) INTO v_space_total, v_space_linked
    FROM sofia.space_industry WHERE company IS NOT NULL;

    SELECT COUNT(*), COUNT(organization_id) INTO v_tech_total, v_tech_linked
    FROM sofia.tech_jobs WHERE company IS NOT NULL;

    RAISE NOTICE '';
    RAISE NOTICE '📈 FINAL COVERAGE:';
    RAISE NOTICE '   funding_rounds:  %/%', v_funding_linked, v_funding_total;
    RAISE NOTICE '   space_industry:  %/%', v_space_linked, v_space_total;
    RAISE NOTICE '   tech_jobs:       %/%', v_tech_linked, v_tech_total;
END $$;
