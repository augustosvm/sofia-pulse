#!/usr/bin/env bash
#
# Health Check Runner for Phase 3 Recovered Collectors
# Runs SQL healthcheck and saves results
# Returns exit 1 if any collector is unhealthy
#

set -euo pipefail

cd "$(dirname "$0")/../.."

# Create outputs directory
mkdir -p outputs/health

# Load environment
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

# Date stamp
DATE=$(date +%Y%m%d_%H%M%S)
TXT_OUTPUT="outputs/health/collectors_health_${DATE}.txt"
JSON_OUTPUT="outputs/health/collectors_health_${DATE}.json"

echo "================================================================================
PHASE 3 COLLECTORS - HEALTH CHECK
================================================================================
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Checking 4 collectors:
  1. world-sports
  2. hdx-humanitarian
  3. sports-regional
  4. women-brazil

================================================================================
" | tee "$TXT_OUTPUT"

# Run SQL healthcheck
PGPASSWORD="${POSTGRES_PASSWORD:-SofiaPulse2025Secure@DB}" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -U "${POSTGRES_USER:-sofia}" \
    -d "${POSTGRES_DB:-sofia_db}" \
    -f scripts/health/collectors-healthcheck.sql \
    2>&1 | tee -a "$TXT_OUTPUT"

echo "
================================================================================
HEALTH CHECK COMPLETE
Output saved to: $TXT_OUTPUT
================================================================================" | tee -a "$TXT_OUTPUT"

# Check if any collector has 0 records in last 24h
UNHEALTHY=$(PGPASSWORD="${POSTGRES_PASSWORD:-SofiaPulse2025Secure@DB}" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -U "${POSTGRES_USER:-sofia}" \
    -d "${POSTGRES_DB:-sofia_db}" \
    -t -c "
    SELECT COUNT(*) FROM (
        SELECT 1 WHERE (SELECT COUNT(*) FROM sofia.world_sports_data WHERE collected_at >= NOW() - INTERVAL '24 hours') = 0
        UNION ALL
        SELECT 1 WHERE (SELECT COUNT(*) FROM sofia.hdx_humanitarian_data WHERE collected_at >= NOW() - INTERVAL '24 hours') = 0
        UNION ALL
        SELECT 1 WHERE (SELECT COUNT(*) FROM sofia.sports_regional WHERE collected_at >= NOW() - INTERVAL '24 hours') = 0
        UNION ALL
        SELECT 1 WHERE (SELECT COUNT(*) FROM sofia.women_brazil_data WHERE collected_at >= NOW() - INTERVAL '24 hours') = 0
    ) x;
" | tr -d ' ')

if [[ "$UNHEALTHY" -gt 0 ]]; then
    echo "
⚠️  WARNING: $UNHEALTHY collector(s) have no data in the last 24 hours!
" | tee -a "$TXT_OUTPUT"
    exit 1
else
    echo "
✅ All collectors healthy (data in last 24 hours)
" | tee -a "$TXT_OUTPUT"
    exit 0
fi
