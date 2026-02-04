#!/bin/bash
# Sofia Pulse - LLM Enrichment + Cross-Signals Pipeline
# Runs daily to enrich HackerNews items and rebuild cross-signals
#
# Usage: bash scripts/run-enrichment-and-cross-signals.sh [--limit 200]

set -e

cd "$(dirname "$0")/.."

# Load environment variables
set -a
source .env 2>/dev/null || true
set +a

# Parse arguments
LIMIT=200
if [ "$1" = "--limit" ]; then
    LIMIT=$2
fi

echo "====================================================================="
echo "SOFIA PULSE - ENRICHMENT + CROSS-SIGNALS PIPELINE"
echo "====================================================================="
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Limit: $LIMIT items"
echo "====================================================================="
echo ""

# Step 1: Enrich HackerNews items
echo "[1/3] Enriching HackerNews items..."
python3 scripts/enrich-hackernews-items-gemini.py --limit $LIMIT
ENRICH_EXIT=$?

if [ $ENRICH_EXIT -ne 0 ]; then
    echo "⚠️  Enrichment failed with exit code $ENRICH_EXIT"
    exit $ENRICH_EXIT
fi

echo ""
echo "[2/3] Refreshing materialized view..."

# Step 2: Refresh materialized view
PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -c "REFRESH MATERIALIZED VIEW sofia.news_items_high_impact;" \
    -c "SELECT COUNT(*) as high_impact_items FROM sofia.news_items_high_impact;"

REFRESH_EXIT=$?

if [ $REFRESH_EXIT -ne 0 ]; then
    echo "⚠️  Materialized view refresh failed with exit code $REFRESH_EXIT"
    exit $REFRESH_EXIT
fi

echo ""
echo "[3/3] Rebuilding cross-signals..."

# Step 3: Rebuild cross-signals
python3 scripts/build-cross-signals.py --window-days 7
BUILD_EXIT=$?

if [ $BUILD_EXIT -ne 0 ]; then
    echo "⚠️  Cross-signals build failed with exit code $BUILD_EXIT"
    exit $BUILD_EXIT
fi

echo ""
echo "====================================================================="
echo "✅ PIPELINE COMPLETE"
echo "====================================================================="
echo "Outputs:"
echo "  - outputs/cross_signals.json"
echo ""
cat outputs/cross_signals.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Insights: {len(d[\"insights\"])}')"
cat outputs/cross_signals.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Observations: {len(d[\"observations\"])}')"
cat outputs/cross_signals.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Sources used: {len([s for s in d[\"sources\"] if s[\"status\"] == \"ok\"])}')"
echo "====================================================================="
