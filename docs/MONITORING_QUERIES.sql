-- ============================================================================
-- QUERIES DE MONITORAMENTO - PATCH NO_TRACKING
-- ============================================================================
-- Usar estas queries para monitorar o sistema após o patch
-- Data: 2026-02-19
-- ============================================================================

-- 1. VERIFICAR DUPLICATAS (últimas 24 horas)
-- Resultado esperado: 0 rows
SELECT
  collector_name,
  date_trunc('hour', started_at) as hour,
  COUNT(*) as duplicates
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY collector_name, date_trunc('hour', started_at)
HAVING COUNT(*) > 1
ORDER BY hour DESC, duplicates DESC;

-- ============================================================================

-- 2. DISTRIBUIÇÃO DE STATUS (últimas 24 horas)
-- Resultado esperado: Apenas 'running' e 'completed' (NÃO 'success')
SELECT
  status,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY status
ORDER BY count DESC;

-- ============================================================================

-- 3. VERIFICAR CAMPOS NULL (indicador de legacy)
-- Resultado esperado: 0 rows (todos devem ter ok e saved preenchidos)
SELECT
  id,
  collector_name,
  status,
  ok,
  saved,
  started_at
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
  AND (ok IS NULL OR saved IS NULL)
ORDER BY started_at DESC
LIMIT 20;

-- ============================================================================

-- 4. HEALTH CHECK - Execuções recentes (últimas 2 horas)
SELECT
  collector_name,
  COUNT(*) as runs,
  SUM(CASE WHEN ok = true THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN ok = false THEN 1 ELSE 0 END) as failed,
  SUM(saved) as total_saved,
  ROUND(AVG(duration_ms) / 1000.0, 2) as avg_duration_sec
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '2 hours'
  AND status = 'completed'
GROUP BY collector_name
ORDER BY runs DESC;

-- ============================================================================

-- 5. TIMELINE - Execuções por hora (últimas 24h)
SELECT
  date_trunc('hour', started_at) as hour,
  COUNT(*) as total_runs,
  SUM(CASE WHEN ok = true THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN ok = false THEN 1 ELSE 0 END) as failed,
  SUM(saved) as total_saved
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', started_at)
ORDER BY hour DESC;

-- ============================================================================

-- 6. TOP ERRORS (últimas 24h)
SELECT
  error_code,
  COUNT(*) as occurrences,
  array_agg(DISTINCT collector_name) as affected_collectors
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
  AND error_code IS NOT NULL
GROUP BY error_code
ORDER BY occurrences DESC
LIMIT 10;

-- ============================================================================

-- 7. COLLECTORS SEM EXECUÇÃO (últimas 24h)
-- Compara com lista esperada de collectors ativos
WITH expected_collectors AS (
  SELECT unnest(ARRAY[
    'jobs-adzuna', 'jobs-jooble', 'himalayas', 'remoteok',
    'jobs-infojobs-brasil', 'jobs-catho', 'arxiv', 'github'
  ]) as collector_name
)
SELECT
  e.collector_name,
  COALESCE(r.last_run, 'NEVER') as last_run,
  COALESCE(r.run_count, 0) as run_count_24h
FROM expected_collectors e
LEFT JOIN (
  SELECT
    collector_name,
    MAX(started_at)::text as last_run,
    COUNT(*) as run_count
  FROM sofia.collector_runs
  WHERE started_at >= NOW() - INTERVAL '24 hours'
  GROUP BY collector_name
) r ON e.collector_name = r.collector_name
ORDER BY run_count_24h ASC, last_run ASC;

-- ============================================================================

-- 8. COMPARAÇÃO ANTES/DEPOIS DO PATCH
-- Comparar registros dos últimos 7 dias antes do patch vs últimas 24h
WITH before_patch AS (
  SELECT
    COUNT(*) as total_runs,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as legacy_tracking,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as new_tracking,
    COUNT(CASE WHEN ok IS NULL THEN 1 END) as null_ok_count
  FROM sofia.collector_runs
  WHERE started_at >= '2026-02-12'::date
    AND started_at < '2026-02-19'::date
),
after_patch AS (
  SELECT
    COUNT(*) as total_runs,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as legacy_tracking,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as new_tracking,
    COUNT(CASE WHEN ok IS NULL THEN 1 END) as null_ok_count
  FROM sofia.collector_runs
  WHERE started_at >= '2026-02-19'::date
)
SELECT
  'BEFORE PATCH (7 days)' as period,
  total_runs,
  legacy_tracking,
  new_tracking,
  null_ok_count
FROM before_patch
UNION ALL
SELECT
  'AFTER PATCH (24h)' as period,
  total_runs,
  legacy_tracking,
  new_tracking,
  null_ok_count
FROM after_patch;

-- ============================================================================
-- FIM DAS QUERIES DE MONITORAMENTO
-- ============================================================================
