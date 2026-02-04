#!/usr/bin/env bash
#
# Install Phase 3 Recovered Collectors into Crontab
# Safely adds 4 new cron entries without removing existing ones
#

set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================================
PHASE 3 COLLECTORS - CRON INSTALLATION
================================================================================
"

# Backup current crontab
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# Empty crontab" > "$BACKUP_FILE"
echo "✅ Current crontab backed up to: $BACKUP_FILE"

# Check if entries already exist
if crontab -l 2>/dev/null | grep -q "SofiaPulse Phase3:"; then
    echo "⚠️  Phase 3 collectors already in crontab. Skipping installation."
    echo "To reinstall, remove the '# SofiaPulse Phase3:' lines manually first."
    exit 0
fi

# Create temp file with new entries
TEMP_CRON="/tmp/sofia-phase3-cron.txt"
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "" > "$TEMP_CRON"

# Add new entries
cat >> "$TEMP_CRON" <<'EOF'

# ================================================================================
# SofiaPulse Phase3: Recovered Collectors (women, sports, humanitarian)
# Added: 2026-02-04
# Schedule: Daily at 03:10-03:40 UTC (00:10-00:40 BRT)
# ================================================================================

# Women Brazil Data (IBGE, IPEA, DataSUS) - 03:10 UTC
10 3 * * * cd ~/sofia-pulse && bash scripts/run-python-collector.sh women-brazil scripts/collect-women-brazil.py

# HDX Humanitarian Data (UNHCR, WFP, MSF) - 03:20 UTC
20 3 * * * cd ~/sofia-pulse && bash scripts/run-python-collector.sh hdx-humanitarian scripts/collect-hdx-humanitarian.py

# Sports Regional (17 sports federations) - 03:30 UTC
30 3 * * * cd ~/sofia-pulse && bash scripts/run-python-collector.sh sports-regional scripts/collect-sports-regional.py

# World Sports Data (WHO, Eurostat, World Bank) - 03:40 UTC
40 3 * * * cd ~/sofia-pulse && bash scripts/run-python-collector.sh world-sports scripts/collect-world-sports.py

# Health Check for Phase 3 Collectors - 04:00 UTC
0 4 * * * cd ~/sofia-pulse && bash scripts/health/run-healthcheck.sh >> ~/sofia-pulse/outputs/health/healthcheck.log 2>&1

EOF

# Install new crontab
crontab "$TEMP_CRON"

echo "
✅ Phase 3 collectors installed in crontab!

New entries added:
  03:10 UTC - women-brazil
  03:20 UTC - hdx-humanitarian
  03:30 UTC - sports-regional
  03:40 UTC - world-sports
  04:00 UTC - healthcheck

Backup saved to: $BACKUP_FILE
Temp file: $TEMP_CRON (safe to delete)

================================================================================
VERIFY INSTALLATION
================================================================================
"

crontab -l | grep -A 10 "SofiaPulse Phase3:"

echo "
================================================================================
To rollback:
  crontab $BACKUP_FILE

To verify logs:
  ls -lh outputs/cron/
  tail -f outputs/cron/women-brazil.log
================================================================================"
