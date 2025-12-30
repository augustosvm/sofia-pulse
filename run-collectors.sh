#!/bin/bash
# Sofia Pulse Collector Runner
# Runs all collectors and logs output

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

LOG_FILE="logs/collectors-$(date +%Y%m%d-%H%M%S).log"

echo "🚀 Starting collectors at $(date)" | tee -a "$LOG_FILE"

# Fast collectors (run every hour)
COLLECTORS=(
    "github"
    "hackernews"
    "stackoverflow"
    "himalayas"
    "remoteok"
    "ai-companies"
    "universities"
    "ngos"
    "yc-companies"
    "nvd"
    "cisa"
    "gdelt"
    "mdic-regional"
    "fiesp-data"
)

SUCCESS=0
FAILED=0

for collector in "${COLLECTORS[@]}"; do
    echo "[$((SUCCESS+FAILED+1))/${#COLLECTORS[@]}] Running: $collector" | tee -a "$LOG_FILE"
    
    if timeout 300 npx tsx scripts/collect.ts "$collector" >> "$LOG_FILE" 2>&1; then
        echo "  ✅ Success" | tee -a "$LOG_FILE"
        ((SUCCESS++))
    else
        echo "  ❌ Failed" | tee -a "$LOG_FILE"
        ((FAILED++))
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "✅ Completed: $SUCCESS/${#COLLECTORS[@]}" | tee -a "$LOG_FILE"
echo "❌ Failed: $FAILED/${#COLLECTORS[@]}" | tee -a "$LOG_FILE"
echo "Finished at $(date)" | tee -a "$LOG_FILE"

# Keep only last 7 days of logs
find logs -name "collectors-*.log" -mtime +7 -delete
