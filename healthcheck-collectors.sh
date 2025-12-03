#!/bin/bash
################################################################################
# SOFIA PULSE - COLLECTORS HEALTHCHECK
# Verifica status de todos os coletores e detecta problemas
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "🏥 SOFIA PULSE COLLECTORS HEALTHCHECK"
echo "════════════════════════════════════════════════════════════════"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Diretório de logs
LOG_DIR="/var/log/sofia/collectors"
mkdir -p "$LOG_DIR"

# Collectors a verificar
COLLECTORS=(
    "collect-github-trending.ts"
    "collect-github-niches.ts"
    "collect-hackernews.ts"
    "collect-reddit-tech.ts"
    "collect-npm-stats.ts"
    "collect-pypi-stats.ts"
    "collect-arxiv-ai.ts"
    "collect-openalex.ts"
    "collect-nih-grants.ts"
    "collect-socioeconomic.py"
    "collect-cybersecurity.py"
    "collect-space-launches.py"
    "collect-ai-regulation.py"
    "collect-gdelt.py"
    "collect-commodity-prices.py"
    "collect-energy-global.py"
)

FAILED=0
TOTAL=0

for collector in "${COLLECTORS[@]}"; do
    TOTAL=$((TOTAL + 1))
    LOG_FILE="$LOG_DIR/${collector}.log"

    if [[ ! -f "$LOG_FILE" ]]; then
        echo "❌ $collector — LOG NOT FOUND"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Verificar última execução
    LAST_RUN=$(tail -20 "$LOG_FILE" | grep -i "finished\|completed\|success" | tail -1)
    LAST_ERROR=$(tail -20 "$LOG_FILE" | grep -i "error\|failed" | tail -1)

    if [[ -z "$LAST_RUN" ]] && [[ -n "$LAST_ERROR" ]]; then
        echo "⚠️  $collector — LAST RUN FAILED"
        echo "   Error: $(echo $LAST_ERROR | cut -c1-80)"
        FAILED=$((FAILED + 1))
    elif [[ -z "$LAST_RUN" ]]; then
        echo "🟡 $collector — NO RECENT SUCCESS"
        FAILED=$((FAILED + 1))
    else
        echo "✅ $collector — OK"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo "Total collectors: $TOTAL"
echo "Healthy: $((TOTAL - FAILED))"
echo "Failed: $FAILED"
echo ""

if [[ $FAILED -gt 0 ]]; then
    echo "⚠️  WARNING: $FAILED collectors need attention!"
    exit 1
else
    echo "✅ ALL COLLECTORS HEALTHY"
    exit 0
fi
