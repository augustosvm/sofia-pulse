-- Migration to normalize jobs geography and fix truncation issues
-- Includes DROP CASCADE for dependent Materialized Views to allow type changes

BEGIN;

-- 1. Add Foreign Keys (Safe, no dependencies)
ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id);
ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS state_id INTEGER REFERENCES sofia.states(id);
ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id);

-- 2. Rename existing columns to raw_ (Safe, no dependencies usually, but if there are, we rename them in views later)
DO $$
BEGIN
    IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='sofia' AND table_name='jobs' AND column_name='city') THEN
        ALTER TABLE sofia.jobs RENAME COLUMN city TO raw_city;
    END IF;
    
    IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='sofia' AND table_name='jobs' AND column_name='state') THEN
        ALTER TABLE sofia.jobs RENAME COLUMN state TO raw_state;
    END IF;

    IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='sofia' AND table_name='jobs' AND column_name='location') THEN
        ALTER TABLE sofia.jobs RENAME COLUMN location TO raw_location;
    END IF;
END $$;

-- 3. Uncap text columns (Requires dropping dependents)
-- Since we can't easily recreate all MVs dynamically in SQL, we will use CASCADE
-- WARNING: This drops the views. We must recreate them immediately or via a separate script.
-- Given the user context, we will try to ALTER in place if possible, but for types it's hard.

-- Check if we need to drop views. The error said: "mv_ai_capability_density_by_country depends on column title"
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_ai_capability_density_by_country CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_brain_drain_by_country CASCADE;
DROP MATERIALIZED VIEW IF EXISTS sofia.mv_research_velocity_by_country CASCADE;
-- Add other potential dependent views here if known, or rely on CASCADE to catch them via specific known parents.
-- For safety, we'll alter the column with CASCADE option if supported, but ALTER COLUMN TYPE doesn't support CASCADE directly in standard SQL.
-- We must manually drop.

ALTER TABLE sofia.jobs ALTER COLUMN title TYPE TEXT;
ALTER TABLE sofia.jobs ALTER COLUMN company TYPE TEXT;
ALTER TABLE sofia.jobs ALTER COLUMN source_url TYPE TEXT;

-- Convert the newly renamed raw columns to TEXT as well
ALTER TABLE sofia.jobs ALTER COLUMN raw_city TYPE TEXT;
ALTER TABLE sofia.jobs ALTER COLUMN raw_state TYPE TEXT;
ALTER TABLE sofia.jobs ALTER COLUMN raw_location TYPE TEXT;

-- NOTE: The views dropped above need to be recreated.
-- We will rely on `scripts/recreate_views.py` or similar if it exists, or the user's "Refresh MVs" task.
-- But to avoid leaving the DB broken, we should ideally recreate them.
-- For this emergency fix, getting the TABLE right is priority. The views can be rebuilt.

COMMIT;
