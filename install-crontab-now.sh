#!/bin/bash
################################################################################
# Sofia Pulse - Install Crontab NOW (No Confirmation)
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📅 INSTALLING CRONTAB - NO CONFIRMATION NEEDED"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we're on the server (not WSL)
if [[ "$PWD" == /mnt/c/* ]]; then
    echo "⚠️  WARNING: You're on Windows/WSL, not the Ubuntu server!"
    echo "   Crontab should be installed on the server at /home/ubuntu/sofia-pulse"
    echo ""
    echo "   To install on the server, SSH into it first:"
    echo "   ssh ubuntu@YOUR_SERVER_IP"
    echo "   cd /home/ubuntu/sofia-pulse"
    echo "   bash install-crontab-now.sh"
    echo ""
    exit 1
fi

# Make scripts executable
chmod +x collect-fast-apis.sh 2>/dev/null || true
chmod +x collect-limited-apis-with-alerts.sh 2>/dev/null || true
chmod +x run-mega-analytics-with-alerts.sh 2>/dev/null || true
chmod +x send-email-mega.sh 2>/dev/null || true

# Backup current crontab
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"

echo "📋 Current crontab backed up to: $BACKUP_FILE"
echo ""

# Get the current working directory for the crontab
SOFIA_DIR="$PWD"

# Create new crontab
cat > /tmp/sofia-crontab.txt << EOF
# ============================================================================
# SOFIA PULSE - Distributed Schedule WITH WHATSAPP ALERTS
# ============================================================================
#
# Schedule:
# - 10:00 UTC (07:00 BRT) - Fast APIs (no WhatsApp yet)
# - 16:00 UTC (13:00 BRT) - Limited APIs + WhatsApp summary
# - 22:00 UTC (19:00 BRT) - Analytics + Email + WhatsApp
#
# WhatsApp notifications:
# - After limited APIs collection (success/failure summary)
# - After analytics (23 reports status)
# - After email sent (confirmation + report count)
# - On any failure (instant alert)
# ============================================================================

# Morning: Fast APIs (Monday-Friday at 10:00 UTC)
0 10 * * 1-5 cd ${SOFIA_DIR} && bash collect-fast-apis.sh >> /var/log/sofia-fast-apis.log 2>&1

# Afternoon: Limited APIs WITH ALERTS (Monday-Friday at 16:00 UTC)
0 16 * * 1-5 cd ${SOFIA_DIR} && bash collect-limited-apis-with-alerts.sh >> /var/log/sofia-limited-apis.log 2>&1

# Evening: Analytics + Email WITH ALERTS (Monday-Friday at 22:00 UTC)
0 22 * * 1-5 cd ${SOFIA_DIR} && bash run-mega-analytics-with-alerts.sh && bash send-email-mega.sh >> /var/log/sofia-analytics.log 2>&1

# Weekly cleanup (Sunday at 02:00 UTC)
0 2 * * 0 find ${SOFIA_DIR}/analytics -name "*.txt" -mtime +30 -delete

EOF

echo "════════════════════════════════════════════════════════════════"
echo "📄 NEW CRONTAB PREVIEW"
echo "════════════════════════════════════════════════════════════════"
cat /tmp/sofia-crontab.txt
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Apply crontab without confirmation
crontab /tmp/sofia-crontab.txt

echo "✅ Crontab installed successfully!"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📅 SCHEDULE SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🌅 10:00 UTC (07:00 BRT) - Fast APIs"
echo "   └─ World Bank, EIA, HackerNews, NPM, PyPI"
echo ""
echo "☀️  16:00 UTC (13:00 BRT) - Limited APIs + WhatsApp"
echo "   └─ GitHub, Reddit, OpenAlex, NIH, Patents"
echo "   └─ 📱 WhatsApp summary after collection"
echo ""
echo "🌙 22:00 UTC (19:00 BRT) - Analytics + Email + WhatsApp"
echo "   └─ 23 reports generated"
echo "   └─ Email sent with all reports and CSVs"
echo "   └─ 📱 WhatsApp alerts"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏰ VERIFY INSTALLATION:"
echo ""
echo "   crontab -l"
echo ""
echo "📝 MONITOR LOGS:"
echo ""
echo "   tail -f /var/log/sofia-limited-apis.log"
echo "   tail -f /var/log/sofia-analytics.log"
echo ""
echo "🧪 TEST MANUALLY:"
echo ""
echo "   bash collect-fast-apis.sh"
echo "   bash collect-limited-apis-with-alerts.sh"
echo "   bash run-mega-analytics-with-alerts.sh && bash send-email-mega.sh"
echo ""
