#!/bin/bash
# Sofia Pulse - GA4 BigQuery Collector
# Collects Google Analytics 4 events from BigQuery export
# Run daily at 16:00 UTC (13:00 BRT)

set -e

cd "$(dirname "$0")"

echo "========================================"
echo "GA4 BigQuery Collector"
echo "Started: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "========================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "[OK] Loaded .env"
else
    echo "[ERROR] .env file not found"
    exit 1
fi

# Verify service account JSON exists
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "[ERROR] GOOGLE_APPLICATION_CREDENTIALS not set in .env"
    exit 1
fi

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "[ERROR] Service account JSON not found: $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

echo "[OK] Service account: $GOOGLE_APPLICATION_CREDENTIALS"
echo ""

# Export credentials for BigQuery client
export GOOGLE_APPLICATION_CREDENTIALS

# Run collector (last 7 days by default)
echo "[INFO] Running GA4 collector..."
python3 scripts/collect_ga4_bigquery.py --days 7

echo ""
echo "========================================"
echo "GA4 BigQuery Collector Complete"
echo "Finished: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "========================================"
