#!/bin/bash
# Docker Hub Collector with WhatsApp Alerts
# Executes collector and sends notification with results

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="logs/docker-stats.log"
TEMP_OUTPUT="/tmp/docker-stats-$(date +%s).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "🐳 Docker Hub Collector" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Run collector and capture output
if npx tsx scripts/collect-docker-stats.ts 2>&1 | tee -a "$LOG_FILE" "$TEMP_OUTPUT"; then

    # Extract stats from output
    INSERTED=$(grep "images updated" "$TEMP_OUTPUT" | grep -oP '\d+(?= images updated)' || echo "0")
    TOTAL=$(grep "Total records:" "$TEMP_OUTPUT" | grep -oP '\d+' || echo "0")
    UNIQUE=$(grep "Unique images:" "$TEMP_OUTPUT" | grep -oP '\d+' || echo "0")

    echo "" | tee -a "$LOG_FILE"
    echo "✅ Collection completed successfully" | tee -a "$LOG_FILE"
    echo "   Inserted: $INSERTED images" | tee -a "$LOG_FILE"
    echo "   Total records: $TOTAL" | tee -a "$LOG_FILE"
    echo "   Unique images: $UNIQUE" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"

    # Send WhatsApp notification
    if command -v python3 &> /dev/null && [ -f "scripts/utils/whatsapp_notifier.py" ]; then
        MESSAGE="🐳 *Docker Hub Collector*

✅ Success
📊 *Inserted*: $INSERTED images
📈 *Total records*: $TOTAL
🎯 *Unique images*: $UNIQUE

⏰ $(date '+%Y-%m-%d %H:%M UTC')"

        python3 scripts/utils/whatsapp_notifier.py "$MESSAGE" 2>&1 | tee -a "$LOG_FILE"
    fi

    EXIT_CODE=0
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ Collection FAILED" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"

    # Send failure alert
    if command -v python3 &> /dev/null && [ -f "scripts/utils/whatsapp_notifier.py" ]; then
        python3 scripts/utils/whatsapp_notifier.py "❌ *Docker Hub Collector FAILED*

Check logs: logs/docker-stats.log

⏰ $(date '+%Y-%m-%d %H:%M UTC')" 2>&1 | tee -a "$LOG_FILE"
    fi

    EXIT_CODE=1
fi

# Cleanup
rm -f "$TEMP_OUTPUT"

echo "Finished: $(date)" | tee -a "$LOG_FILE"
exit $EXIT_CODE
