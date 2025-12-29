-- Cleanup duplicate organizations
-- Keeps the oldest ID (lowest) for each normalized_name
-- Updates all foreign keys to point to the kept ID

DO $$
DECLARE
    duplicate_count INTEGER;
    merged_count INTEGER := 0;
BEGIN
    RAISE NOTICE '🔍 Finding duplicate organizations...';

    -- Count duplicates
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT normalized_name
        FROM sofia.organizations
        GROUP BY normalized_name
        HAVING COUNT(*) > 1
    ) dupes;

    RAISE NOTICE 'Found % groups of duplicates', duplicate_count;

    IF duplicate_count = 0 THEN
        RAISE NOTICE '✅ No duplicates found!';
        RETURN;
    END IF;

    -- Create temp table with duplicates to merge
    CREATE TEMP TABLE duplicates_to_merge AS
    WITH ranked_orgs AS (
        SELECT
            id,
            normalized_name,
            name,
            ROW_NUMBER() OVER (PARTITION BY normalized_name ORDER BY id ASC) as rn
        FROM sofia.organizations
    )
    SELECT
        id as duplicate_id,
        normalized_name,
        FIRST_VALUE(id) OVER (PARTITION BY normalized_name ORDER BY id ASC) as keep_id
    FROM ranked_orgs
    WHERE normalized_name IN (
        SELECT normalized_name
        FROM sofia.organizations
        GROUP BY normalized_name
        HAVING COUNT(*) > 1
    );

    RAISE NOTICE '📋 Duplicates to merge: %', (SELECT COUNT(*) FROM duplicates_to_merge WHERE duplicate_id != keep_id);

    -- Update all tables with organization_id foreign keys
    -- funding_rounds
    UPDATE sofia.funding_rounds f
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE f.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ funding_rounds: % records updated', merged_count;

    -- space_industry
    UPDATE sofia.space_industry s
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE s.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ space_industry: % records updated', merged_count;

    -- jobs
    UPDATE sofia.jobs j
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE j.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ jobs: % records updated', merged_count;

    -- market_data_brazil
    UPDATE sofia.market_data_brazil m
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE m.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ market_data_brazil: % records updated', merged_count;

    -- market_data_nasdaq
    UPDATE sofia.market_data_nasdaq m
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE m.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ market_data_nasdaq: % records updated', merged_count;

    -- global_universities_progress
    UPDATE sofia.global_universities_progress g
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE g.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ global_universities_progress: % records updated', merged_count;

    -- world_ngos
    UPDATE sofia.world_ngos w
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE w.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ world_ngos: % records updated', merged_count;

    -- hdx_humanitarian_data
    UPDATE sofia.hdx_humanitarian_data h
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE h.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ hdx_humanitarian_data: % records updated', merged_count;

    -- hkex_ipos
    UPDATE sofia.hkex_ipos h
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE h.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ hkex_ipos: % records updated', merged_count;

    -- startups
    UPDATE sofia.startups s
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE s.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ startups: % records updated', merged_count;

    -- nih_grants
    UPDATE sofia.nih_grants n
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE n.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ nih_grants: % records updated', merged_count;

    -- tech_jobs (if exists)
    UPDATE sofia.tech_jobs t
    SET organization_id = d.keep_id
    FROM duplicates_to_merge d
    WHERE t.organization_id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '  ✅ tech_jobs: % records updated', merged_count;

    -- Now delete the duplicate organizations
    DELETE FROM sofia.organizations o
    USING duplicates_to_merge d
    WHERE o.id = d.duplicate_id
      AND d.duplicate_id != d.keep_id;

    GET DIAGNOSTICS merged_count = ROW_COUNT;
    RAISE NOTICE '';
    RAISE NOTICE '🗑️  Deleted % duplicate organization records', merged_count;

    -- Final stats
    RAISE NOTICE '';
    RAISE NOTICE '✅ Cleanup complete!';
    RAISE NOTICE 'Total organizations now: %', (SELECT COUNT(*) FROM sofia.organizations);

    DROP TABLE duplicates_to_merge;

END $$;
