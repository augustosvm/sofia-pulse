#!/bin/bash

################################################################################
# Sofia Pulse - Update Crontab with Distributed Schedule
################################################################################
#
# Distribui coletas em 3 horários diferentes para evitar rate limits:
#
# 1. 10:00 UTC (07:00 BRT) - Fast APIs (sem rate limit severo)
# 2. 16:00 UTC (13:00 BRT) - Limited APIs (com rate limiting)
# 3. 22:00 UTC (19:00 BRT) - Analytics + Email
#
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make scripts executable
chmod +x collect-fast-apis.sh
chmod +x collect-limited-apis.sh
chmod +x run-mega-analytics.sh
chmod +x send-email-mega.sh

echo "════════════════════════════════════════════════════════════════"
echo "📅 UPDATING CRONTAB - Distributed Schedule"
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
# SOFIA PULSE - Distributed Collection Schedule
# ============================================================================
#
# Strategy: Distribute collections across 3 different times to avoid rate limits
#
# Morning (10:00 UTC / 07:00 BRT):
#   - Fast APIs (no severe rate limits)
#   - World Bank, EIA, OWID, HackerNews, NPM, PyPI
#   - Duration: ~5 minutes
#
# Afternoon (16:00 UTC / 13:00 BRT):
#   - Limited APIs (with rate limiting + exponential backoff)
#   - GitHub, Reddit, OpenAlex, NIH, Patents
#   - Duration: ~10-15 minutes
#
# Evening (22:00 UTC / 19:00 BRT):
#   - Analytics + Email
#   - All analysis + send email with reports
#   - Duration: ~5 minutes
#
# Total: 3 separate runs, avoiding concurrent API calls
# ============================================================================

# Morning: Fast APIs (Monday-Friday at 10:00 UTC)
0 10 * * 1-5 cd /home/ubuntu/sofia-pulse && bash collect-fast-apis.sh >> /var/log/sofia-fast-apis.log 2>&1

# Afternoon: Limited APIs (Monday-Friday at 16:00 UTC)
0 16 * * 1-5 cd /home/ubuntu/sofia-pulse && bash collect-limited-apis.sh >> /var/log/sofia-limited-apis.log 2>&1

# Evening: Analytics + Email (Monday-Friday at 22:00 UTC)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-mega-analytics.sh && bash send-email-mega.sh >> /var/log/sofia-analytics.log 2>&1

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
    echo "📅 SCHEDULE SUMMARY"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🌅 Morning (10:00 UTC / 07:00 BRT) - Monday to Friday"
    echo "   └─ Fast APIs Collection"
    echo "   └─ Duration: ~5 minutes"
    echo "   └─ Log: /var/log/sofia-fast-apis.log"
    echo ""
    echo "☀️  Afternoon (16:00 UTC / 13:00 BRT) - Monday to Friday"
    echo "   └─ Limited APIs Collection (with rate limiting)"
    echo "   └─ Duration: ~10-15 minutes"
    echo "   └─ Log: /var/log/sofia-limited-apis.log"
    echo ""
    echo "🌙 Evening (22:00 UTC / 19:00 BRT) - Monday to Friday"
    echo "   └─ Analytics + Email"
    echo "   └─ Duration: ~5 minutes"
    echo "   └─ Log: /var/log/sofia-analytics.log"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🎯 BENEFITS OF DISTRIBUTED SCHEDULE:"
    echo ""
    echo "✅ APIs collected at different times (avoid rate limits)"
    echo "✅ Automatic retry with exponential backoff"
    echo "✅ Rate limit monitoring via headers"
    echo "✅ Separate logs for debugging"
    echo "✅ Analytics run after all data is collected"
    echo ""
    echo "📊 EXPECTED IMPROVEMENT:"
    echo ""
    echo "   GitHub:  60% → 95%+ success rate"
    echo "   Reddit:  0% → 90%+ success rate"
    echo "   NPM:     50% → 90%+ success rate"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "📝 NEXT STEPS:"
    echo ""
    echo "1. Monitor first run:"
    echo "   tail -f /var/log/sofia-fast-apis.log"
    echo ""
    echo "2. Check rate limit warnings:"
    echo "   grep 'Rate limit' /var/log/sofia-*.log"
    echo ""
    echo "3. View crontab:"
    echo "   crontab -l"
    echo ""
    echo "4. Restore backup if needed:"
    echo "   crontab $BACKUP_FILE"
    echo ""
else
    echo ""
    echo "❌ Crontab update cancelled"
    echo "   Backup saved at: $BACKUP_FILE"
    echo ""
fi
