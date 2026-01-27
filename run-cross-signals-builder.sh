#!/bin/bash
# Run Cross Signals Builder (with materialized view refresh)
#
# This script:
# 1. Refreshes materialized views (news_items_high_impact, vscode_extensions_7d_deltas)
# 2. Runs the cross-signals builder
# 3. Validates the output JSON
#
# Should run daily BEFORE email is sent (e.g., 21:30 UTC if email is 22:00 UTC)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "Sofia Pulse - Cross Signals Builder"
echo "=================================================="
echo "Started: $(date)"
echo ""

# Load environment
if [ -f .env ]; then
    source .env
else
    echo "⚠️  .env file not found, using environment variables"
fi

# Step 1: Refresh materialized views
echo "📊 Step 1: Refreshing materialized views..."

psql -h "${DB_HOST:-localhost}" \
     -p "${DB_PORT:-5432}" \
     -U "${DB_USER:-postgres}" \
     -d "${DB_NAME:-sofia}" \
     -c "REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.news_items_high_impact;" \
     2>/dev/null || {
    echo "⚠️  Could not refresh news_items_high_impact (table may not exist yet)"
}

psql -h "${DB_HOST:-localhost}" \
     -p "${DB_PORT:-5432}" \
     -U "${DB_USER:-postgres}" \
     -d "${DB_NAME:-sofia}" \
     -c "REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.vscode_extensions_7d_deltas;" \
     2>/dev/null || {
    echo "⚠️  Could not refresh vscode_extensions_7d_deltas (table may not exist yet)"
}

echo "✅ Materialized views refreshed"
echo ""

# Step 2: Run cross-signals builder
echo "🔗 Step 2: Building cross-signals..."

python3 scripts/build-cross-signals.py --window-days 7

if [ $? -eq 0 ]; then
    echo "✅ Cross-signals built successfully"
else
    echo "❌ Cross-signals builder failed!"
    exit 1
fi
echo ""

# Step 3: Validate JSON output
echo "🔍 Step 3: Validating output..."

if [ -f outputs/cross_signals.json ]; then
    # Check if it's valid JSON
    if python3 -m json.tool outputs/cross_signals.json > /dev/null 2>&1; then
        echo "✅ cross_signals.json is valid JSON"

        # Count insights
        INSIGHTS_COUNT=$(python3 -c "import json; data=json.load(open('outputs/cross_signals.json')); print(data['coverage']['total_insights'])")
        OBS_COUNT=$(python3 -c "import json; data=json.load(open('outputs/cross_signals.json')); print(data['coverage']['total_observations'])")
        SOURCES_USED=$(python3 -c "import json; data=json.load(open('outputs/cross_signals.json')); print(data['coverage']['sources_used'])")

        echo "   Insights: $INSIGHTS_COUNT"
        echo "   Observations: $OBS_COUNT"
        echo "   Sources Used: $SOURCES_USED"
    else
        echo "❌ cross_signals.json is not valid JSON!"
        exit 1
    fi
else
    echo "❌ outputs/cross_signals.json not found!"
    exit 1
fi
echo ""

echo "=================================================="
echo "✅ Cross-signals pipeline completed successfully"
echo "Finished: $(date)"
echo "=================================================="
