#!/bin/bash

################################################################################
# Sofia Pulse - Update Crontab WITH WHATSAPP ALERTS
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make scripts executable
chmod +x collect-fast-apis.sh
chmod +x collect-limited-apis-with-alerts.sh
chmod +x run-mega-analytics-with-alerts.sh
chmod +x send-email-mega.sh

echo "════════════════════════════════════════════════════════════════"
echo "📅 UPDATING CRONTAB - WITH WHATSAPP ALERTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Backup current crontab
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# New crontab" > "$BACKUP_FILE"

echo "📋 Current crontab backed up to: $BACKUP_FILE"
echo ""

# Create new crontab
cat > /tmp/new-crontab.txt << 'EOF'
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
0 10 * * 1-5 cd /home/ubuntu/sofia-pulse && bash collect-fast-apis.sh >> /var/log/sofia-fast-apis.log 2>&1

# Afternoon: Limited APIs WITH ALERTS (Monday-Friday at 16:00 UTC)
0 16 * * 1-5 cd /home/ubuntu/sofia-pulse && bash collect-limited-apis-with-alerts.sh >> /var/log/sofia-limited-apis.log 2>&1

# Evening: Analytics + Email WITH ALERTS (Monday-Friday at 22:00 UTC)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-mega-analytics-with-alerts.sh && bash send-email-mega.sh >> /var/log/sofia-analytics.log 2>&1

# Weekly cleanup (Sunday at 02:00 UTC)
0 2 * * 0 find /home/ubuntu/sofia-pulse/analytics -name "*.txt" -mtime +30 -delete

EOF

echo "════════════════════════════════════════════════════════════════"
echo "📄 NEW CRONTAB PREVIEW"
echo "════════════════════════════════════════════════════════════════"
cat /tmp/new-crontab.txt
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Prompt for confirmation
read -p "Apply this crontab? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Apply new crontab
    crontab /tmp/new-crontab.txt
    echo ""
    echo "✅ Crontab updated successfully!"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "📅 SCHEDULE SUMMARY WITH WHATSAPP"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🌅 10:00 UTC (07:00 BRT) - Fast APIs"
    echo "   └─ World Bank, EIA, HackerNews, NPM, PyPI"
    echo "   └─ No WhatsApp alerts (too early, low failure rate)"
    echo ""
    echo "☀️  16:00 UTC (13:00 BRT) - Limited APIs + WhatsApp Summary"
    echo "   └─ GitHub, Reddit, OpenAlex, NIH, Patents"
    echo "   └─ 📱 WhatsApp: Success/failure summary after collection"
    echo ""
    echo "🌙 22:00 UTC (19:00 BRT) - Analytics + Email + WhatsApp"
    echo "   └─ 23 reports generated"
    echo "   └─ 📱 WhatsApp: Analytics summary (which reports succeeded)"
    echo "   └─ Email sent with all reports and CSVs"
    echo "   └─ 📱 WhatsApp: Email sent confirmation"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "📱 WHATSAPP NOTIFICATIONS YOU'LL RECEIVE:"
    echo ""
    echo "1. 16:00 UTC (13:00 BRT) - After collection:"
    echo "   ✅ Limited APIs Collection"
    echo "   📊 Total: 10"
    echo "   ✅ Success: 8"
    echo "   ❌ Failed: 2"
    echo ""
    echo "2. 22:00 UTC (19:00 BRT) - After analytics:"
    echo "   ✅ Analytics Complete"
    echo "   📊 Total: 23"
    echo "   ✅ Success: 23"
    echo "   ❌ Failed: 0"
    echo ""
    echo "3. 22:05 UTC (19:05 BRT) - After email:"
    echo "   ✅ Sofia Pulse Report Sent"
    echo "   📧 Email: augustosvm@gmail.com"
    echo "   📄 Reports: 23"
    echo "   📊 CSVs: 15"
    echo ""
    echo "4. ANY TIME - On failure:"
    echo "   ❌ Collector Failed / Analytics Failed"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "⏰ NEXT AUTOMATIC NOTIFICATION:"
    echo ""

    # Calculate next run time
    current_hour=$(date -u +%H)
    current_day=$(date +%u)  # 1-7 (Mon-Sun)

    if [ "$current_day" -ge 1 ] && [ "$current_day" -le 5 ]; then
        # Weekday
        if [ "$current_hour" -lt 16 ]; then
            echo "   📱 Today at 16:00 UTC (13:00 BRT) - Collection summary"
        elif [ "$current_hour" -lt 22 ]; then
            echo "   📱 Today at 22:00 UTC (19:00 BRT) - Analytics + Email"
        else
            echo "   📱 Tomorrow at 16:00 UTC (13:00 BRT) - Collection summary"
        fi
    else
        # Weekend
        echo "   📱 Monday at 16:00 UTC (13:00 BRT) - Collection summary"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "📝 MONITOR LOGS:"
    echo ""
    echo "   tail -f /var/log/sofia-limited-apis.log"
    echo "   tail -f /var/log/sofia-analytics.log"
    echo ""
    echo "📝 VIEW CRONTAB:"
    echo ""
    echo "   crontab -l"
    echo ""
else
    echo ""
    echo "❌ Crontab update cancelled"
    echo "   Backup saved at: $BACKUP_FILE"
    echo ""
fi
