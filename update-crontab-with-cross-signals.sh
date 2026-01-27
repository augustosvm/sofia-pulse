#!/bin/bash
# Update Crontab - Add Cross Signals Builder
#
# This script adds Cross Signals builder to cron schedule.
# Schedule: 21:30 UTC (30 minutes before email at 22:00 UTC)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "Sofia Pulse - Update Crontab with Cross Signals"
echo "=================================================="
echo ""

# Create new crontab entries
CRON_FILE=$(mktemp)

cat > "$CRON_FILE" << 'EOF'
# Sofia Pulse - Complete Schedule
# User: sofia-pulse
# Updated: 2026-01-27 (Added Cross Signals)

# Morning: Fast APIs (10:00 UTC / 07:00 BRT)
0 10 * * 1-5 cd ~/sofia-pulse && bash collect-fast-apis.sh >> ~/sofia-pulse/logs/collect-fast.log 2>&1

# Afternoon: Limited APIs with rate limiting (16:00 UTC / 13:00 BRT)
0 16 * * 1-5 cd ~/sofia-pulse && bash collect-limited-apis-with-alerts.sh >> ~/sofia-pulse/logs/collect-limited.log 2>&1

# Evening: Cross Signals Builder (21:30 UTC / 18:30 BRT) ⭐ NEW
30 21 * * 1-5 cd ~/sofia-pulse && bash run-cross-signals-builder.sh >> ~/sofia-pulse/logs/cross-signals.log 2>&1

# Evening: Analytics (22:00 UTC / 19:00 BRT)
0 22 * * 1-5 cd ~/sofia-pulse && bash run-mega-analytics-with-alerts.sh >> ~/sofia-pulse/logs/analytics.log 2>&1

# Evening: Email with Cross Signals (22:05 UTC / 19:05 BRT)
5 22 * * 1-5 cd ~/sofia-pulse && bash send-email-mega.sh >> ~/sofia-pulse/logs/email.log 2>&1

# Weekly: Cleanup old logs (Sunday 00:00 UTC)
0 0 * * 0 find ~/sofia-pulse/logs -name "*.log" -mtime +30 -delete

EOF

echo "📝 New crontab entries:"
cat "$CRON_FILE"
echo ""

# Backup current crontab
echo "💾 Backing up current crontab..."
crontab -l > ~/sofia-pulse-crontab-backup-$(date +%Y%m%d-%H%M%S).txt 2>/dev/null || true

# Install new crontab
echo "⚙️  Installing new crontab..."
crontab "$CRON_FILE"

# Cleanup
rm "$CRON_FILE"

echo "✅ Crontab updated successfully!"
echo ""
echo "📅 New Schedule:"
echo "   10:00 UTC - Fast APIs collection"
echo "   16:00 UTC - Limited APIs collection (with rate limiting)"
echo "   21:30 UTC - Cross Signals Builder ⭐ NEW"
echo "   22:00 UTC - Analytics + Reports"
echo "   22:05 UTC - Email with Cross Signals"
echo ""
echo "To view current crontab: crontab -l"
echo "To restore backup: crontab ~/sofia-pulse-crontab-backup-YYYYMMDD-HHMMSS.txt"
echo ""
echo "=================================================="
