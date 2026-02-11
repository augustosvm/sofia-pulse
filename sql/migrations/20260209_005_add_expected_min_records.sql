-- Sofia Skills Kit - Add expected_min_records validation
-- Permite detectar collectors que "rodaram mas vieram vazios"

BEGIN;

-- Adicionar coluna para mínimo esperado de registros
ALTER TABLE sofia.collector_inventory
  ADD COLUMN IF NOT EXISTS expected_min_records INTEGER NOT NULL DEFAULT 1;

-- Adicionar flag para tolerar dias vazios (ex: segurança pode ter dias sem eventos)
ALTER TABLE sofia.collector_inventory
  ADD COLUMN IF NOT EXISTS allow_empty BOOLEAN NOT NULL DEFAULT FALSE;

-- View: Collectors que rodaram hoje mas salvaram menos que o mínimo esperado
-- Complementa v_missing_runs_today para detectar "ok vazio"
CREATE OR REPLACE VIEW sofia.v_empty_runs_today AS
SELECT
  i.collector_id,
  i.expected_min_records,
  r.run_id,
  r.saved,
  r.fetched,
  r.finished_at,
  r.ok
FROM sofia.collector_inventory i
JOIN LATERAL (
  SELECT *
  FROM sofia.collector_runs cr
  WHERE cr.collector_name = i.collector_id
    AND cr.started_at::date = CURRENT_DATE
  ORDER BY cr.started_at DESC
  LIMIT 1
) r ON TRUE
WHERE i.status = 'active'
  AND i.schedule = 'daily'
  AND i.allow_empty = false
  AND r.ok = true
  AND COALESCE(r.saved, 0) < i.expected_min_records;

COMMIT;
