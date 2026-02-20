#\!/usr/bin/env bash
# Quick health check for NO_TRACKING patch

set -euo pipefail

PGPASSWORD='SofiaPulse2025Secure@DB'

echo "════════════════════════════════════════════════════════════════"
echo "🔍 TRACKING HEALTH CHECK - Post NO_TRACKING Patch"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Duplicatas
echo "📊 1. DUPLICATAS (últimas 24h):"
echo "   Esperado: 0 rows"
echo ""
PGPASSWORD="$PGPASSWORD" psql -h localhost -U sofia -d sofia_db -c "
SELECT
  collector_name,
  date_trunc('hour', started_at) as hour,
  COUNT(*) as duplicates
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY collector_name, date_trunc('hour', started_at)
HAVING COUNT(*) > 1
ORDER BY hour DESC, duplicates DESC;
" 2>/dev/null || echo "   ⚠️  Erro ao consultar banco"

echo ""
echo "────────────────────────────────────────────────────────────────"

# 2. Status distribution
echo "📊 2. DISTRIBUIÇÃO DE STATUS (últimas 24h):"
echo "   Esperado: Apenas 'running' e 'completed' (SEM 'success')"
echo ""
PGPASSWORD="$PGPASSWORD" psql -h localhost -U sofia -d sofia_db -c "
SELECT
  status,
  COUNT(*) as count
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY status
ORDER BY count DESC;
" 2>/dev/null || echo "   ⚠️  Erro ao consultar banco"

echo ""
echo "────────────────────────────────────────────────────────────────"

# 3. NULL check
echo "📊 3. CAMPOS NULL (indicador de legacy tracking):"
echo "   Esperado: 0 rows"
echo ""
PGPASSWORD="$PGPASSWORD" psql -h localhost -U sofia -d sofia_db -c "
SELECT COUNT(*) as null_fields_count
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
  AND (ok IS NULL OR saved IS NULL);
" 2>/dev/null || echo "   ⚠️  Erro ao consultar banco"

echo ""
echo "────────────────────────────────────────────────────────────────"

# 4. Recent runs
echo "📊 4. EXECUÇÕES RECENTES (últimas 2h):"
echo ""
PGPASSWORD="$PGPASSWORD" psql -h localhost -U sofia -d sofia_db -c "
SELECT
  collector_name,
  COUNT(*) as runs,
  SUM(CASE WHEN ok = true THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN ok = false THEN 1 ELSE 0 END) as failed
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '2 hours'
  AND status = 'completed'
GROUP BY collector_name
ORDER BY runs DESC
LIMIT 10;
" 2>/dev/null || echo "   ⚠️  Erro ao consultar banco"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Health check completo"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 Para queries detalhadas, consulte:"
echo "   /home/ubuntu/sofia-pulse/docs/MONITORING_QUERIES.sql"
echo ""
