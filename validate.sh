#!/bin/bash
#
# Sofia Pulse - Validate
# Valida que o sistema está rodando corretamente
#

set -e

echo "=================================================="
echo "SOFIA PULSE - VALIDAÇÃO DO SISTEMA"
echo "=================================================="
echo ""

PROJECT_DIR="/Users/augustovespermann/sofia-pulse"
cd "$PROJECT_DIR" || exit 1

# Carregar env
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql://sofia:sofia123strong@localhost:5432/sofia_db"
fi

source .venv/bin/activate

echo "[1/5] Validando crontab..."
crontab -l | grep -q "sync_expected_set" && echo "  ✅ sync_expected_set agendado" || echo "  ❌ sync_expected_set NÃO agendado"
crontab -l | grep -q "daily_pipeline" && echo "  ✅ daily_pipeline agendado" || echo "  ❌ daily_pipeline NÃO agendado"
crontab -l | grep -q "run_and_verify" && echo "  ✅ run_and_verify agendado" || echo "  ❌ run_and_verify NÃO agendado"
echo ""

echo "[2/5] Validando diretório de logs..."
if [ -d "/var/log/sofia" ]; then
    echo "  ✅ /var/log/sofia existe"
    ls -lh /var/log/sofia/*.log 2>/dev/null | tail -5 || echo "  ⚠️ Nenhum log ainda"
else
    echo "  ❌ /var/log/sofia NÃO existe"
fi
echo ""

echo "[3/5] Validando expected set..."
if [ -f "config/daily_expected_collectors.json" ]; then
    echo "  ✅ Expected set existe"
    python3 -c "
import json
with open('config/daily_expected_collectors.json') as f:
    config = json.load(f)
print(f\"  Total esperado: {config['_stats']['total_allowed']}\")
print(f\"  Required: {len(config['groups']['required'])}\")
print(f\"  GA4: {len(config['groups']['ga4'])}\")
"
else
    echo "  ❌ Expected set NÃO existe"
fi
echo ""

echo "[4/5] Validando banco de dados (últimas 24h)..."
python3 << 'EOF'
import psycopg2
import os
from datetime import datetime

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Runs últimas 24h
cur.execute("""
SELECT COUNT(*),
       COUNT(DISTINCT collector_name) as collectors,
       SUM(CASE WHEN saved > 0 THEN saved ELSE 0 END) as total_saved,
       MAX(started_at AT TIME ZONE 'America/Sao_Paulo') as last_run_brt
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '24 hours'
""")

count, collectors, total_saved, last = cur.fetchone()
print(f"  Total runs: {count}")
print(f"  Collectors distintos: {collectors}")
print(f"  Total saved: {total_saved}")
print(f"  Última execução (BRT): {last}")

if count == 0:
    print("  ❌ NENHUM RUN NAS ÚLTIMAS 24H")
elif count < 10:
    print("  ⚠️ Poucos runs (< 10)")
else:
    print("  ✅ Sistema rodando")

cur.close()
conn.close()
EOF
echo ""

echo "[5/5] Validando GA4..."
python3 << 'EOF'
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
SELECT collector_name, COUNT(*) as runs, MAX(saved) as max_saved, ok
FROM sofia.collector_runs
WHERE collector_name LIKE 'ga4-%'
  AND started_at >= NOW() - INTERVAL '7 days'
GROUP BY collector_name, ok
ORDER BY collector_name, ok DESC
""")

rows = cur.fetchall()
if not rows:
    print("  ❌ GA4 NÃO RODOU NOS ÚLTIMOS 7 DIAS")
else:
    for row in rows:
        status = "✅" if row[3] else "❌"
        print(f"  {status} {row[0]}: {row[1]} runs, max saved={row[2]}")

cur.close()
conn.close()
EOF
echo ""

echo "=================================================="
echo "FIM DA VALIDAÇÃO"
echo "=================================================="
