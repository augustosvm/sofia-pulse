#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"

echo "⏰ Atualizando cron com FASE 2..."
echo ""

BACKUP_FILE="$HOME/crontab-backup-phase2-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"

cat > /tmp/sofia-crontab-phase2.txt << CRONEOF
# Sofia Pulse - Complete Automation (FASE 2)
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# TECH INTELLIGENCE
0 8 * * * cd $SOFIA_DIR && npm run collect:github-trending >> /var/log/sofia-github.log 2>&1
30 8 * * * cd $SOFIA_DIR && npm run collect:hackernews >> /var/log/sofia-hn.log 2>&1
0 9 * * * cd $SOFIA_DIR && npm run collect:gdelt >> /var/log/sofia-gdelt.log 2>&1

# FINANCE & RESEARCH
0 21 * * 1-5 cd $SOFIA_DIR && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1
0 20 * * * cd $SOFIA_DIR && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1
5 20 * * * cd $SOFIA_DIR && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1
10 20 * * * cd $SOFIA_DIR && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1
0 1 * * * cd $SOFIA_DIR && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1
0 2 * * 1-5 cd $SOFIA_DIR && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1
0 3 * * 1 cd $SOFIA_DIR && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1
0 4 1 * * cd $SOFIA_DIR && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1
0 5 * * 1 cd $SOFIA_DIR && npm run collect:cardboard >> /var/log/sofia-cardboard.log 2>&1
0 6 * * * cd $SOFIA_DIR && npm run collect:ipo-calendar >> /var/log/sofia-ipo.log 2>&1
0 7 * * * cd $SOFIA_DIR && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# INSIGHTS COMPLETOS (FASE 2)
0 22 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && bash run-insights.sh >> /var/log/sofia-insights.log 2>&1

# EMAIL (FASE 2)
0 23 * * 1-5 cd $SOFIA_DIR && bash send-email-phase2.sh >> /var/log/sofia-email.log 2>&1

# DARK HORSES REPORT (Mensal - dia 1)
0 0 1 * * cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 analytics/dark-horses-report.py >> /var/log/sofia-darkhorse.log 2>&1

# BACKUPS
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh 2>/dev/null || true
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh 2>/dev/null || true
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh 2>/dev/null || true
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh 2>/dev/null || true
0 4 * * * cd $SOFIA_DIR && ./scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1 || true
CRONEOF

sed -i "s|\$SOFIA_DIR|$SOFIA_DIR|g" /tmp/sofia-crontab-phase2.txt

echo "📊 Comparação:"
echo ""
diff -u "$BACKUP_FILE" /tmp/sofia-crontab-phase2.txt || true
echo ""

read -p "Instalar cron atualizado? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    crontab /tmp/sofia-crontab-phase2.txt
    echo "✅ Cron atualizado!"
    echo ""
    echo "📋 Jobs instalados:"
    crontab -l | grep -c "cd $SOFIA_DIR" || echo "0"
else
    echo "⏭️  Instalação cancelada"
    echo "   Para instalar: crontab /tmp/sofia-crontab-phase2.txt"
fi
