#!/usr/bin/env bash
#
# Phase 3 Recovered Collectors - Runner Script
# Runs all 4 collectors recovered in Phase 3
# Usage: bash scripts/collect-phase3-recovered.sh
#

set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================================
PHASE 3 RECOVERED COLLECTORS - BATCH RUN
================================================================================
Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Collectors:
  1. hdx-humanitarian
  2. sports-regional
  3. world-sports
  4. women-brazil

================================================================================
"

FAILURES=0

# 1. HDX Humanitarian (fastest)
echo "▶ [1/4] Running hdx-humanitarian..."
if bash scripts/run-python-collector.sh hdx-humanitarian scripts/collect-hdx-humanitarian.py; then
    echo "✅ hdx-humanitarian completed"
else
    echo "❌ hdx-humanitarian failed"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 2. Sports Regional (medium)
echo "▶ [2/4] Running sports-regional..."
if bash scripts/run-python-collector.sh sports-regional scripts/collect-sports-regional.py; then
    echo "✅ sports-regional completed"
else
    echo "❌ sports-regional failed"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 3. Women Brazil (medium)
echo "▶ [3/4] Running women-brazil..."
if bash scripts/run-python-collector.sh women-brazil scripts/collect-women-brazil.py; then
    echo "✅ women-brazil completed"
else
    echo "❌ women-brazil failed"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 4. World Sports (longest - timeout expected)
echo "▶ [4/4] Running world-sports..."
if bash scripts/run-python-collector.sh world-sports scripts/collect-world-sports.py; then
    echo "✅ world-sports completed"
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 124 ]]; then
        echo "⚠️  world-sports timed out (expected - very large dataset)"
    else
        echo "❌ world-sports failed"
        FAILURES=$((FAILURES + 1))
    fi
fi
echo ""

echo "================================================================================
BATCH RUN COMPLETE
Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Failures: $FAILURES/4
================================================================================"

exit $FAILURES
