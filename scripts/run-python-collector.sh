#!/usr/bin/env bash
#
# Generic Python Collector Runner
# Usage: bash scripts/run-python-collector.sh <collector-name> <script-path>
# Example: bash scripts/run-python-collector.sh world-sports scripts/collect-world-sports.py
#

set -euo pipefail

COLLECTOR_NAME="${1:-}"
SCRIPT_PATH="${2:-}"

if [[ -z "$COLLECTOR_NAME" || -z "$SCRIPT_PATH" ]]; then
    echo "❌ Usage: $0 <collector-name> <script-path>"
    exit 1
fi

# Change to project root
cd "$(dirname "$0")/.."

# Create logs directory if needed
mkdir -p outputs/cron

# Lock file to prevent concurrent runs
LOCK_FILE="/tmp/sofia-collector-${COLLECTOR_NAME}.lock"

# Log file
LOG_FILE="outputs/cron/${COLLECTOR_NAME}.log"

# Function to cleanup lock on exit
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Try to acquire lock (with timeout)
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "⚠️  [$(date -u +%Y-%m-%dT%H:%M:%SZ)] Another instance of $COLLECTOR_NAME is running. Exiting." | tee -a "$LOG_FILE"
    exit 0
fi

echo "================================================================================
SOFIA PULSE - $COLLECTOR_NAME COLLECTOR
================================================================================
Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Script: $SCRIPT_PATH
Log: $LOG_FILE
================================================================================" | tee -a "$LOG_FILE"

# Load environment variables
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

# Run collector with timeout (10 minutes)
EXIT_CODE=0
timeout 600 python3 "$SCRIPT_PATH" 2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?

# Check exit code
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "
✅ SUCCESS - $COLLECTOR_NAME completed successfully
Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Exit Code: $EXIT_CODE
================================================================================" | tee -a "$LOG_FILE"
elif [[ $EXIT_CODE -eq 124 ]]; then
    echo "
⚠️  TIMEOUT - $COLLECTOR_NAME timed out after 10 minutes
Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Exit Code: $EXIT_CODE
================================================================================" | tee -a "$LOG_FILE"
else
    echo "
❌ FAILED - $COLLECTOR_NAME failed with exit code $EXIT_CODE
Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Exit Code: $EXIT_CODE
================================================================================" | tee -a "$LOG_FILE"
fi

exit $EXIT_CODE
