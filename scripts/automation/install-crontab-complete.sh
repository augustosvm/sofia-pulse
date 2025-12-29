#!/bin/bash
################################################################################
# Sofia Pulse - Install Complete Crontab (ALL 55 Collectors)
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📅 INSTALLING COMPLETE CRONTAB (ALL 55 COLLECTORS)"
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
    echo "   bash install-crontab-complete.sh"
    echo ""
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x collect-all-complete.sh 2>/dev/null || true
chmod +x run-mega-analytics-with-alerts.sh 2>/dev/null || true
chmod +x send-email-mega.sh 2>/dev/null || true
chmod +x run-migration-nih-fix.sh 2>/dev/null || true
echo ""

# Backup current crontab
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"

echo "📋 Current crontab backed up to: $BACKUP_FILE"
echo ""

# Get the current working directory for the crontab
SOFIA_DIR="$PWD"

# Create new crontab with ALL 55 collectors
cat > /tmp/sofia-crontab-complete.txt << EOF
# ============================================================================
# SOFIA PULSE - COMPLETE AUTOMATION (ALL 55 COLLECTORS + ANALYTICS)
# ============================================================================
#
# Schedule:
# - 09:00 UTC (06:00 BRT) - Database migrations (if needed)
# - 10:00 UTC (07:00 BRT) - ALL 55 collectors (1.5-2 hours)
# - 22:00 UTC (19:00 BRT) - Analytics + Email + WhatsApp
#
# Features:
# - All 55 collectors running (not just 22)
# - Detailed error logging per collector
# - WhatsApp alerts with error details (SQL, API, Network)
# - Structured logs in /var/log/sofia/collectors/
# ============================================================================

# Database migrations (Monday morning before collection)
0 9 * * 1 cd ${SOFIA_DIR} && bash run-migration-nih-fix.sh >> /var/log/sofia-migrations.log 2>&1

# COMPLETE Collection - ALL 55 collectors (Monday-Friday at 10:00 UTC)
# Expected duration: 1.5-2 hours (includes rate limiting delays)
# Groups: Fast APIs, GitHub, Research, Patents, Brazil, International, Women, Social, Sports
0 10 * * 1-5 cd ${SOFIA_DIR} && bash collect-all-complete.sh >> /var/log/sofia-all-collectors.log 2>&1

# Analytics + Email + WhatsApp (Monday-Friday at 22:00 UTC)
# Runs after collection completes
# Generates 33 reports + sends email + WhatsApp notifications
0 22 * * 1-5 cd ${SOFIA_DIR} && bash run-mega-analytics-with-alerts.sh && bash send-email-mega.sh >> /var/log/sofia-analytics.log 2>&1

# Weekly cleanup (Sunday at 02:00 UTC)
# Removes old report files (>30 days) and old logs (>7 days)
0 2 * * 0 find ${SOFIA_DIR}/analytics -name "*.txt" -mtime +30 -delete && find /var/log/sofia/collectors -name "*.log" -mtime +7 -delete

EOF

echo "════════════════════════════════════════════════════════════════"
echo "📄 NEW CRONTAB PREVIEW"
echo "════════════════════════════════════════════════════════════════"
cat /tmp/sofia-crontab-complete.txt
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Apply crontab without confirmation
crontab /tmp/sofia-crontab-complete.txt

echo "✅ Crontab installed successfully!"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📅 SCHEDULE SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🔧 09:00 UTC (06:00 BRT) Monday - Database Migrations"
echo "   └─ Run NIH VARCHAR fix (if not already applied)"
echo "   └─ Future migrations will run here automatically"
echo ""
echo "📊 10:00 UTC (07:00 BRT) Monday-Friday - ALL 55 Collectors"
echo "   └─ Group 1: Fast APIs (12 collectors)"
echo "   └─ Group 2: GitHub (2 collectors, rate limited)"
echo "   └─ Group 3: Research (5 collectors, rate limited)"
echo "   └─ Group 4: Patents (4 collectors, rate limited)"
echo "   └─ Group 5: International Orgs (8 collectors)"
echo "   └─ Group 6: Women/Gender (6 collectors)"
echo "   └─ Group 7: Brasil Official (6 collectors) 🇧🇷"
echo "   └─ Group 8: Social/Demographics (5 collectors)"
echo "   └─ Group 9: Sports/Olympics (3 collectors)"
echo "   └─ Group 10: Other Specialized (4 collectors)"
echo "   └─ Duration: ~1.5-2 hours (includes rate limit delays)"
echo "   └─ 📱 WhatsApp: Detailed error report with categories"
echo ""
echo "📈 22:00 UTC (19:00 BRT) Monday-Friday - Analytics + Email"
echo "   └─ Generate 33 reports"
echo "   └─ Send email with reports + CSVs"
echo "   └─ 📱 WhatsApp: Analytics summary + email confirmation"
echo ""
echo "🧹 02:00 UTC Sunday - Cleanup"
echo "   └─ Remove old reports (>30 days)"
echo "   └─ Remove old logs (>7 days)"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 COVERAGE:"
echo "   • Collectors: 55/55 (100%) ✅"
echo "   • Brazil data: BACEN, IBGE, IPEA, ComexStat ✅"
echo "   • International: WHO, UNICEF, ILO, WTO, FAO ✅"
echo "   • Gender data: 6 sources ✅"
echo "   • Sports: FIFA, IOC, Olympics ✅"
echo ""
echo "📱 WHATSAPP NOTIFICATIONS:"
echo "   • 10:00 UTC: Collector errors with details (SQL/API/Network)"
echo "   • 22:00 UTC: Analytics summary (23 reports)"
echo "   • 22:05 UTC: Email sent confirmation"
echo ""
echo "📝 MONITOR LOGS:"
echo "   # All collectors (combined)"
echo "   tail -f /var/log/sofia-all-collectors.log"
echo ""
echo "   # Individual collector (detailed)"
echo "   tail -f /var/log/sofia/collectors/bacen-sgs-$(date +%Y-%m-%d).log"
echo "   tail -f /var/log/sofia/collectors/ibge-api-$(date +%Y-%m-%d).log"
echo ""
echo "   # Analytics"
echo "   tail -f /var/log/sofia-analytics.log"
echo ""
echo "   # Migrations"
echo "   tail -f /var/log/sofia-migrations.log"
echo ""
echo "📋 VERIFY CRONTAB:"
echo "   crontab -l"
echo ""
echo "🧪 TEST MANUALLY NOW:"
echo "   # Run migration first (one-time)"
echo "   bash run-migration-nih-fix.sh"
echo ""
echo "   # Run all collectors (takes 1.5-2 hours)"
echo "   bash collect-all-complete.sh"
echo ""
echo "   # Run analytics + email"
echo "   bash run-mega-analytics-with-alerts.sh && bash send-email-mega.sh"
echo ""
echo "⏰ NEXT AUTOMATIC RUNS:"

# Calculate next run times
current_hour=$(date -u +%H)
current_day=$(date +%u)  # 1-7 (Mon-Sun)

echo ""
if [ "$current_day" -eq 1 ]; then
    # Monday
    if [ "$current_hour" -lt 9 ]; then
        echo "   📅 Today at 09:00 UTC (06:00 BRT) - Migrations"
        echo "   📊 Today at 10:00 UTC (07:00 BRT) - Collectors"
        echo "   📈 Today at 22:00 UTC (19:00 BRT) - Analytics"
    elif [ "$current_hour" -lt 10 ]; then
        echo "   📊 Today at 10:00 UTC (07:00 BRT) - Collectors"
        echo "   📈 Today at 22:00 UTC (19:00 BRT) - Analytics"
    elif [ "$current_hour" -lt 22 ]; then
        echo "   📈 Today at 22:00 UTC (19:00 BRT) - Analytics"
    else
        echo "   📊 Tomorrow at 10:00 UTC (07:00 BRT) - Collectors"
    fi
elif [ "$current_day" -ge 2 ] && [ "$current_day" -le 5 ]; then
    # Tuesday-Friday
    if [ "$current_hour" -lt 10 ]; then
        echo "   📊 Today at 10:00 UTC (07:00 BRT) - Collectors"
        echo "   📈 Today at 22:00 UTC (19:00 BRT) - Analytics"
    elif [ "$current_hour" -lt 22 ]; then
        echo "   📈 Today at 22:00 UTC (19:00 BRT) - Analytics"
    else
        echo "   📊 Tomorrow at 10:00 UTC (07:00 BRT) - Collectors"
    fi
else
    # Weekend
    echo "   📅 Next Monday at 09:00 UTC (06:00 BRT) - Migrations"
    echo "   📊 Next Monday at 10:00 UTC (07:00 BRT) - Collectors"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Installation complete! System will run automatically."
echo ""
