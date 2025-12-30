-- Fix orphaned city_id in tech_jobs
-- Set to NULL if the city doesn't exist

DO $$
DECLARE
    orphaned_count INTEGER;
BEGIN
    RAISE NOTICE '🔍 Finding orphaned city_id in tech_jobs...';

    -- Count orphaned
    SELECT COUNT(*) INTO orphaned_count
    FROM sofia.tech_jobs t
    WHERE t.city_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM sofia.cities c
          WHERE c.id = t.city_id
      );

    RAISE NOTICE 'Found % orphaned city_id references', orphaned_count;

    IF orphaned_count = 0 THEN
        RAISE NOTICE '✅ No orphaned city_id found!';
        RETURN;
    END IF;

    -- Set orphaned city_id to NULL
    UPDATE sofia.tech_jobs
    SET city_id = NULL
    WHERE city_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM sofia.cities c
          WHERE c.id = tech_jobs.city_id
      );

    RAISE NOTICE '✅ Fixed % orphaned city_id references (set to NULL)', orphaned_count;

END $$;
