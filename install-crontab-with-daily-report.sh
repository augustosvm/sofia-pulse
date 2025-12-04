#!/bin/bash
################################################################################
# Sofia Pulse - Install Crontab with Daily WhatsApp Reports
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📅 INSTALLING CRONTAB WITH DAILY WHATSAPP REPORTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if on server
if [[ "$PWD" == /mnt/c/* ]]; then
    echo "⚠️  Run on server: ssh ubuntu@SERVER && cd /home/ubuntu/sofia-pulse"
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x run-collectors-with-logging.sh
chmod +x scripts/utils/daily_report_generator.py
chmod +x run-mega-analytics-with-alerts.sh
chmod +x send-email-mega.sh
chmod +x run-migration-nih-fix.sh
echo ""

# Backup
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"
echo "📋 Backup: $BACKUP_FILE"
echo ""

SOFIA_DIR="$PWD"

# Create crontab with daily reports
cat > /tmp/sofia-crontab-with-reports.txt << CRONTAB_EOF
# ============================================================================
# SOFIA PULSE - COMPLETE AUTOMATION WITH DAILY WHATSAPP REPORTS
# ============================================================================
# Features:
# - All 55 collectors grouped by frequency
# - Immediate WhatsApp alerts for CRITICAL errors
# - Daily summary report at 23:00 UTC (20:00 BRT)
# - Analytics + email at 22:00 UTC (19:00 BRT)
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SOFIA_DIR=${SOFIA_DIR}

# ============================================================================
# HOURLY - Every 3 hours (08:00, 11:00, 14:00, 17:00, 20:00 UTC)
# ============================================================================
0 8,11,14,17,20 * * 1-5 cd \$SOFIA_DIR && bash run-collectors-with-logging.sh >> /var/log/sofia/hourly.log 2>&1

# ============================================================================
# DAILY - Once per day at 10:00 UTC (07:00 BRT)
# ============================================================================
0 10 * * 1-5 cd \$SOFIA_DIR && bash run-collectors-with-logging.sh >> /var/log/sofia/daily.log 2>&1

# ============================================================================
# WEEKLY - Mondays at 13:00 UTC (10:00 BRT)
# ============================================================================
0 13 * * 1 cd \$SOFIA_DIR && bash run-collectors-with-logging.sh >> /var/log/sofia/weekly.log 2>&1

# ============================================================================
# MONTHLY - 1st Monday at 14:00 UTC (11:00 BRT)
# ============================================================================
0 14 1-7 * 1 cd \$SOFIA_DIR && bash run-collectors-with-logging.sh >> /var/log/sofia/monthly.log 2>&1

# ============================================================================
# ANALYTICS - Daily at 22:00 UTC (19:00 BRT)
# ============================================================================
0 22 * * 1-5 cd \$SOFIA_DIR && bash run-mega-analytics-with-alerts.sh >> /var/log/sofia/analytics.log 2>&1

# ============================================================================
# EMAIL - Daily at 22:30 UTC (19:30 BRT)
# ============================================================================
30 22 * * 1-5 cd \$SOFIA_DIR && bash send-email-mega.sh >> /var/log/sofia/email.log 2>&1

# ============================================================================
# DAILY WHATSAPP REPORT - 23:00 UTC (20:00 BRT) - After all collection done
# ============================================================================
0 23 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/utils/daily_report_generator.py /var/log/sofia >> /var/log/sofia/daily-report.log 2>&1

# ============================================================================
# MAINTENANCE
# ============================================================================

# Database migrations (Monday 09:00 UTC)
0 9 * * 1 cd \$SOFIA_DIR && bash run-migration-nih-fix.sh >> /var/log/sofia/migrations.log 2>&1

# Cleanup old files (Sunday 02:00 UTC)
0 2 * * 0 cd \$SOFIA_DIR && find analytics -name "*.txt" -mtime +30 -delete && find /var/log/sofia -name "*.log" -mtime +7 -delete 2>/dev/null

CRONTAB_EOF

echo "════════════════════════════════════════════════════════════════"
echo "📄 NEW CRONTAB WITH DAILY REPORTS"
echo "════════════════════════════════════════════════════════════════"
cat /tmp/sofia-crontab-with-reports.txt
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Apply
crontab /tmp/sofia-crontab-with-reports.txt

echo "✅ Crontab installed with daily WhatsApp reports!"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📱 WHATSAPP ALERTS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🚨 IMMEDIATE ALERTS (during collection):"
echo "   • SQL errors (missing table, column, constraint)"
echo "   • API key errors (401, missing key)"
echo "   • Critical failures"
echo ""
echo "📊 DAILY SUMMARY REPORT (23:00 UTC / 20:00 BRT):"
echo "   • Total collectors run"
echo "   • Success count & rate"
echo "   • Failures grouped by category"
echo "   • Top errors with details"
echo "   • Next steps to fix"
echo ""
echo "Example Report:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Sofia Pulse - Relatório Diário"
echo "Data: 03/12/2025 20:00"
echo ""
echo "📊 RESUMO GERAL"
echo "Total: 42 collectors"
echo "✅ Sucesso: 39 (92.9%)"
echo "❌ Falhas: 3"
echo ""
echo "🔴 FALHAS POR CATEGORIA"
echo ""
echo "SQL: Duplicate Key (1):"
echo "• bacen-sgs"
echo "  Duplicate record in bacen_series"
echo ""
echo "API: Forbidden (1):"
echo "• reddit-tech"
echo "  reddit.com blocked request"
echo ""
echo "SQL: Value Too Long (1):"
echo "• nih-grants"
echo "  VARCHAR limit exceeded (50 chars)"
echo ""
echo "📝 PRÓXIMOS PASSOS"
echo "⚠️ CRÍTICO: Corrigir primeiro"
echo "• SQL: Value Too Long: 1 collector(s)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📅 SCHEDULE:"
echo "   08:00, 11:00, 14:00, 17:00, 20:00 UTC - Hourly collectors (7)"
echo "   10:00 UTC - Daily collectors (34)"
echo "   13:00 UTC Mon - Weekly collectors (10)"
echo "   14:00 UTC 1st Mon - Monthly collectors (6)"
echo "   22:00 UTC - Analytics (33 reports)"
echo "   22:30 UTC - Email report"
echo "   23:00 UTC - Daily WhatsApp summary 📱"
echo ""
echo "🧪 TEST DAILY REPORT NOW:"
echo "   source venv-analytics/bin/activate"
echo "   python3 scripts/utils/daily_report_generator.py /var/log/sofia"
echo ""
