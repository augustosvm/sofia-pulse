-- Migration: Drop Old Geographic Columns
-- Remove colunas antigas (city, state, country) após backfill completo
-- APENAS EXECUTE APÓS verificar que 027_backfill_geographic_ids.sql rodou com sucesso!

BEGIN;

-- ============================================================================
-- VERIFICAÇÃO DE SEGURANÇA
-- ============================================================================

DO $$
DECLARE
  jobs_country_coverage NUMERIC;
  funding_country_coverage NUMERIC;
BEGIN
  -- Verificar cobertura antes de apagar
  SELECT ROUND(COUNT(country_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1)
  INTO jobs_country_coverage
  FROM sofia.jobs;

  SELECT ROUND(COUNT(country_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1)
  INTO funding_country_coverage
  FROM sofia.funding_rounds;

  -- Se cobertura < 80%, abortar
  IF jobs_country_coverage < 80 OR funding_country_coverage < 80 THEN
    RAISE EXCEPTION 'Cobertura insuficiente! Jobs: %%, Funding: %%. Execute backfill primeiro!',
      jobs_country_coverage, funding_country_coverage;
  END IF;

  RAISE NOTICE 'Verificação OK. Cobertura: Jobs %, Funding %',
    jobs_country_coverage, funding_country_coverage;
END $$;

-- ============================================================================
-- DROP COLUMNS FROM JOBS
-- ============================================================================

ALTER TABLE sofia.jobs
  DROP COLUMN IF EXISTS city,
  DROP COLUMN IF EXISTS state,
  DROP COLUMN IF EXISTS country;

-- ============================================================================
-- DROP COLUMNS FROM FUNDING_ROUNDS
-- ============================================================================

ALTER TABLE sofia.funding_rounds
  DROP COLUMN IF EXISTS city,
  DROP COLUMN IF EXISTS country;

-- ============================================================================
-- ANALYTICS VIEWS - Se houver views usando essas colunas, recriar aqui
-- ============================================================================

-- Exemplo: Se havia uma view, recriar sem as colunas antigas
-- CREATE OR REPLACE VIEW sofia.vw_jobs_by_location AS
-- SELECT
--   j.id,
--   co.common_name as country,
--   s.name as state,
--   ci.name as city
-- FROM sofia.jobs j
-- LEFT JOIN sofia.countries co ON j.country_id = co.id
-- LEFT JOIN sofia.states s ON j.state_id = s.id
-- LEFT JOIN sofia.cities ci ON j.city_id = ci.id;

COMMIT;

-- Mensagem final
DO $$
BEGIN
  RAISE NOTICE '========================================';
  RAISE NOTICE 'OLD GEOGRAPHIC COLUMNS DROPPED';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Tables updated:';
  RAISE NOTICE '  - sofia.jobs (dropped: city, state, country)';
  RAISE NOTICE '  - sofia.funding_rounds (dropped: city, country)';
  RAISE NOTICE '';
  RAISE NOTICE 'Now using ONLY normalized IDs:';
  RAISE NOTICE '  - country_id -> sofia.countries';
  RAISE NOTICE '  - state_id -> sofia.states';
  RAISE NOTICE '  - city_id -> sofia.cities';
  RAISE NOTICE '========================================';
END $$;
