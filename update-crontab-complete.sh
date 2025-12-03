#!/bin/bash

# ============================================================================
# UPDATE CRONTAB - COMPLETE SCHEDULE
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "UPDATING CRONTAB - COMPLETE SCHEDULE"
echo "════════════════════════════════════════════════════════════════"

SOFIA_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Sofia Pulse directory: $SOFIA_DIR"

# Create logs directory
mkdir -p "$SOFIA_DIR/logs"

# Backup current crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Create new crontab entries
cat > /tmp/sofia_crontab.txt << EOF
# ============================================================================
# SOFIA PULSE - DATA COLLECTION SCHEDULE
# Updated: $(date -u '+%Y-%m-%d %H:%M:%S') UTC
# ============================================================================

# DIÁRIO - Segunda a Sexta
0 10 * * 1-5 cd $SOFIA_DIR && set -a && source .env && set +a && bash collect-fast-apis.sh >> logs/cron-fast.log 2>&1
0 16 * * 1-5 cd $SOFIA_DIR && set -a && source .env && set +a && bash collect-limited-apis-with-alerts.sh >> logs/cron-limited.log 2>&1
0 22 * * 1-5 cd $SOFIA_DIR && set -a && source .env && set +a && bash run-mega-analytics-with-alerts.sh >> logs/cron-analytics.log 2>&1
5 22 * * 1-5 cd $SOFIA_DIR && set -a && source .env && set +a && bash send-email-mega.sh >> logs/cron-email.log 2>&1
10 22 * * 1-5 cd $SOFIA_DIR && set -a && source .env && set +a && python3 send-reports-whatsapp.py >> logs/cron-whatsapp.log 2>&1

# SEMANAL - Domingos
0 8 * * 0 cd $SOFIA_DIR && set -a && source .env && set +a && bash collect-women-data.sh >> logs/cron-women.log 2>&1
0 10 * * 0 cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-world-security.py >> logs/cron-security.log 2>&1
0 11 * * 0 cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-brazil-security.py >> logs/cron-brazil-security.log 2>&1
0 12 * * 0 cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-world-tourism.py >> logs/cron-tourism.log 2>&1
0 13 * * 0 cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-sports-regional.py >> logs/cron-sports.log 2>&1
0 14 * * 0 cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-drugs-data.py >> logs/cron-drugs.log 2>&1

# MENSAL - Dia 1
0 6 1 * * cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-world-ngos.py >> logs/cron-ngos.log 2>&1
0 7 1 * * cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-religion-data.py >> logs/cron-religion.log 2>&1
0 8 1 * * cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-sports-federations.py >> logs/cron-federations.log 2>&1
0 9 1 * * cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-central-banks-women.py >> logs/cron-central-banks.log 2>&1
0 10 1 * * cd $SOFIA_DIR && set -a && source .env && set +a && python3 scripts/collect-brazil-ministries.py >> logs/cron-ministries.log 2>&1
EOF

echo ""
echo "Crontab entries to add:"
cat /tmp/sofia_crontab.txt
echo ""
echo "Installing crontab..."
crontab /tmp/sofia_crontab.txt
echo ""
echo "Done! Verifying:"
crontab -l
