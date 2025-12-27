-- ============================================================================
-- Migration 044: Bulk Backfill Geographic IDs (FAST)
-- ============================================================================
-- Uses pure SQL bulk operations for country_id/state_id/city_id normalization
-- ============================================================================

DO $$
DECLARE
    v_start_time TIMESTAMP;
    v_updated INT;
BEGIN
    v_start_time := clock_timestamp();
    RAISE NOTICE '🌍 Starting bulk geographic backfill...';
    RAISE NOTICE '';

    -- ========================================================================
    -- JOBS TABLE
    -- ========================================================================
    RAISE NOTICE '1️⃣  jobs → country_id';

    UPDATE sofia.jobs j
    SET country_id = c.id
    FROM sofia.countries c
    WHERE j.country_id IS NULL
    AND j.country IS NOT NULL
    AND (
        UPPER(j.country) = c.iso_alpha2
        OR UPPER(j.country) = c.iso_alpha3
        OR LOWER(TRIM(j.country)) = LOWER(c.common_name)
    );

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % jobs', v_updated;

    -- ========================================================================
    -- PERSONS TABLE
    -- ========================================================================
    RAISE NOTICE '2️⃣  persons → country_id';

    UPDATE sofia.persons p
    SET country_id = c.id
    FROM sofia.countries c
    WHERE p.country_id IS NULL
    AND p.country IS NOT NULL
    AND (
        UPPER(p.country) = c.iso_alpha2
        OR UPPER(p.country) = c.iso_alpha3
        OR LOWER(TRIM(p.country)) = LOWER(c.common_name)
    );

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % persons', v_updated;

    -- ========================================================================
    -- SOCIOECONOMIC_INDICATORS
    -- ========================================================================
    RAISE NOTICE '3️⃣  socioeconomic_indicators → country_id';

    UPDATE sofia.socioeconomic_indicators s
    SET country_id = c.id
    FROM sofia.countries c
    WHERE s.country_id IS NULL
    AND (s.country_name IS NOT NULL OR s.country_code IS NOT NULL)
    AND (
        UPPER(COALESCE(s.country_code, '')) = c.iso_alpha2
        OR UPPER(COALESCE(s.country_code, '')) = c.iso_alpha3
        OR LOWER(TRIM(COALESCE(s.country_name, ''))) = LOWER(c.common_name)
    );

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % indicators', v_updated;

    -- ========================================================================
    -- SPACE_INDUSTRY
    -- ========================================================================
    RAISE NOTICE '4️⃣  space_industry → country_id';

    UPDATE sofia.space_industry s
    SET country_id = c.id
    FROM sofia.countries c
    WHERE s.country_id IS NULL
    AND s.country IS NOT NULL
    AND (
        UPPER(s.country) = c.iso_alpha2
        OR UPPER(s.country) = c.iso_alpha3
        OR LOWER(TRIM(s.country)) = LOWER(c.common_name)
    );

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % space records', v_updated;

    -- ========================================================================
    -- TECH_JOBS
    -- ========================================================================
    RAISE NOTICE '5️⃣  tech_jobs → country_id';

    UPDATE sofia.tech_jobs t
    SET country_id = c.id
    FROM sofia.countries c
    WHERE t.country_id IS NULL
    AND t.country IS NOT NULL
    AND (
        UPPER(t.country) = c.iso_alpha2
        OR UPPER(t.country) = c.iso_alpha3
        OR LOWER(TRIM(t.country)) = LOWER(c.common_name)
    );

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % tech jobs', v_updated;

    -- ========================================================================
    -- PORT_TRAFFIC
    -- ========================================================================
    RAISE NOTICE '6️⃣  port_traffic → country_id';

    UPDATE sofia.port_traffic p
    SET country_id = c.id
    FROM sofia.countries c
    WHERE p.country_id IS NULL
    AND p.country_code IS NOT NULL
    AND (
        UPPER(p.country_code) = c.iso_alpha2
        OR UPPER(p.country_code) = c.iso_alpha3
    );

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % port records', v_updated;

    -- ========================================================================
    -- TABLES WITH 0% COVERAGE (Never backfilled)
    -- ========================================================================

    RAISE NOTICE '7️⃣  brazil_security_data → country_id';
    UPDATE sofia.brazil_security_data SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BR');
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % records (all Brazil)', v_updated;

    RAISE NOTICE '8️⃣  women_brazil_data → country_id';
    UPDATE sofia.women_brazil_data SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = 'BR') WHERE country_id IS NULL;
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % records (all Brazil)', v_updated;

    RAISE NOTICE '9️⃣  sports_regional → country_id';
    UPDATE sofia.sports_regional s
    SET country_id = c.id
    FROM sofia.countries c
    WHERE s.country_id IS NULL
    AND s.country_code IS NOT NULL
    AND UPPER(s.country_code) = c.iso_alpha2;
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % sports records', v_updated;

    RAISE NOTICE '🔟 hdx_humanitarian_data → country_id (array matching)';
    UPDATE sofia.hdx_humanitarian_data h
    SET country_id = c.id
    FROM sofia.countries c
    WHERE h.country_id IS NULL
    AND h.country_codes IS NOT NULL
    AND c.iso_alpha3 = ANY(h.country_codes);
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % humanitarian records', v_updated;

    RAISE NOTICE '1️⃣1️⃣ comexstat_trade → country_id';
    UPDATE sofia.comexstat_trade t
    SET country_id = c.id
    FROM sofia.countries c
    WHERE t.country_id IS NULL
    AND (t.country_name IS NOT NULL OR t.country_code IS NOT NULL)
    AND (
        UPPER(COALESCE(t.country_code, '')) = c.iso_alpha2
        OR LOWER(TRIM(COALESCE(t.country_name, ''))) = LOWER(c.common_name)
    );
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RAISE NOTICE '   ✅ Updated % trade records', v_updated;

    -- ========================================================================
    -- SUMMARY
    -- ========================================================================
    RAISE NOTICE '';
    RAISE NOTICE '✅ Bulk geographic backfill complete!';
    RAISE NOTICE '   Duration: %', (clock_timestamp() - v_start_time);

END $$;

-- Show final coverage
DO $$
DECLARE
    v_table TEXT;
    v_total INT;
    v_with_id INT;
    v_pct NUMERIC;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📈 FINAL COVERAGE:';

    FOR v_table IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'sofia'
        AND column_name = 'country_id'
        AND table_name IN (
            'jobs', 'persons', 'socioeconomic_indicators',
            'space_industry', 'tech_jobs', 'port_traffic',
            'brazil_security_data', 'women_brazil_data',
            'sports_regional', 'hdx_humanitarian_data', 'comexstat_trade'
        )
    LOOP
        EXECUTE format('SELECT COUNT(*), COUNT(country_id) FROM sofia.%I', v_table)
        INTO v_total, v_with_id;

        IF v_total > 0 THEN
            v_pct := ROUND(100.0 * v_with_id / v_total, 1);
            RAISE NOTICE '   %: %/%',
                RPAD(v_table, 30),
                v_with_id,
                v_total;
        END IF;
    END LOOP;
END $$;
