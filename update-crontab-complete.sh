#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔄 VERIFICAR E ATUALIZAR CRONTAB - Sofia Pulse Complete"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Detect environment
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
    USER_HOME="/home/ubuntu"
elif [ -d "/home/user/sofia-pulse" ]; then
    SOFIA_DIR="/home/user/sofia-pulse"
    USER_HOME="/home/user"
else
    echo "❌ Sofia Pulse directory not found!"
    exit 1
fi

echo "📍 Sofia Pulse: $SOFIA_DIR"
echo "📍 User Home: $USER_HOME"
echo ""

# Check current crontab
echo "🔍 Verificando crontab atual..."
echo ""

CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")

if [ -z "$CURRENT_CRONTAB" ]; then
    echo "⚠️  Nenhum crontab encontrado"
    HAS_CRONTAB=false
else
    echo "✅ Crontab atual:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    crontab -l | grep -v "^#" | grep -v "^$" || echo "  (apenas comentários)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    HAS_CRONTAB=true
fi

echo ""

# Check if run-all-with-venv.sh exists
if [ ! -f "$SOFIA_DIR/run-all-with-venv.sh" ]; then
    echo "⚠️  run-all-with-venv.sh not found in $SOFIA_DIR"
    echo "   Creating it..."

    cat > "$SOFIA_DIR/run-all-with-venv.sh" << 'EOFSCRIPT'
#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 RUN ALL COLLECTORS WITH VENV"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Detect environment
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
elif [ -d "/home/user/sofia-pulse" ]; then
    SOFIA_DIR="/home/user/sofia-pulse"
else
    echo "❌ Sofia Pulse directory not found!"
    exit 1
fi

cd "$SOFIA_DIR"

# Activate venv
if [ -d "venv-analytics" ]; then
    echo "✅ Activating venv-analytics..."
    source venv-analytics/bin/activate
else
    echo "❌ venv-analytics not found! Run ./install-python-deps.sh first"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 CREATING TABLES"
echo "════════════════════════════════════════════════════════════════════════════════"
python3 create-tables-python.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 RUNNING COLLECTORS"
echo "════════════════════════════════════════════════════════════════════════════════"

echo ""
echo "⚡ Electricity Consumption..."
python3 scripts/collect-electricity-consumption.py

echo ""
echo "🚢 Port Traffic..."
python3 scripts/collect-port-traffic.py

echo ""
echo "📈 Commodity Prices..."
python3 scripts/collect-commodity-prices.py

echo ""
echo "💾 Semiconductor Sales..."
python3 scripts/collect-semiconductor-sales.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ ALL COLLECTORS COMPLETED!"
echo "════════════════════════════════════════════════════════════════════════════════"
EOFSCRIPT

    chmod +x "$SOFIA_DIR/run-all-with-venv.sh"
    echo "   ✅ Created run-all-with-venv.sh"
fi

echo ""

# Backup current crontab
if [ "$HAS_CRONTAB" = true ]; then
    BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
    echo "📋 Fazendo backup do crontab atual..."
    crontab -l > "$BACKUP_FILE"
    echo "   ✅ Backup: $BACKUP_FILE"
    echo ""
fi

# Create new crontab
echo "🔧 Criando novo crontab..."
echo ""

cat > /tmp/crontab-sofia-complete.txt << CRONEOF
# ============================================================================
# SOFIA PULSE - Complete Data Collection System
# ============================================================================

# ============================================================================
# DATA COLLECTION - Node.js Collectors
# ============================================================================

# GitHub Trending - Diariamente às 8:00 UTC
0 8 * * * cd $SOFIA_DIR && npm run collect:github-trending >> /var/log/sofia-github.log 2>&1

# HackerNews - Diariamente às 8:30 UTC
30 8 * * * cd $SOFIA_DIR && npm run collect:hackernews >> /var/log/sofia-hn.log 2>&1

# NPM Stats - Diariamente às 9:00 UTC
0 9 * * * cd $SOFIA_DIR && npm run collect:npm-stats >> /var/log/sofia-npm.log 2>&1

# PyPI Stats - Diariamente às 9:30 UTC
30 9 * * * cd $SOFIA_DIR && npm run collect:pypi-stats >> /var/log/sofia-pypi.log 2>&1

# Reddit Tech - Diariamente às 10:00 UTC
0 10 * * * cd $SOFIA_DIR && npm run collect:reddit-tech >> /var/log/sofia-reddit.log 2>&1

# ArXiv AI - Diariamente às 20:00 UTC
0 20 * * * cd $SOFIA_DIR && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1

# OpenAlex - Diariamente às 20:05 UTC
5 20 * * * cd $SOFIA_DIR && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1

# AI Companies - Diariamente às 20:10 UTC
10 20 * * * cd $SOFIA_DIR && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1

# Cybersecurity - Diariamente às 11:00 UTC
0 11 * * * cd $SOFIA_DIR && npm run collect:cybersecurity >> /var/log/sofia-cybersecurity.log 2>&1

# Space Industry - Diariamente às 11:30 UTC
30 11 * * * cd $SOFIA_DIR && npm run collect:space-industry >> /var/log/sofia-space.log 2>&1

# AI Regulation - Diariamente às 12:00 UTC
0 12 * * * cd $SOFIA_DIR && npm run collect:ai-regulation >> /var/log/sofia-ai-regulation.log 2>&1

# GDELT Events - Diariamente às 12:30 UTC
30 12 * * * cd $SOFIA_DIR && npm run collect:gdelt >> /var/log/sofia-gdelt.log 2>&1

# Finance - Seg-Sex às 21:00 UTC
0 21 * * 1-5 cd $SOFIA_DIR && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1

# Patents - Diariamente às 1:00 UTC
0 1 * * * cd $SOFIA_DIR && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1

# HKEX - Seg-Sex às 2:00 UTC
0 2 * * 1-5 cd $SOFIA_DIR && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1

# NIH Grants - Segundas às 3:00 UTC
0 3 * * 1 cd $SOFIA_DIR && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1

# Asia Universities - Dia 1 de cada mês às 4:00 UTC
0 4 1 * * cd $SOFIA_DIR && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1

# IPO Calendar - Diariamente às 6:00 UTC
0 6 * * * cd $SOFIA_DIR && npm run collect:ipo-calendar >> /var/log/sofia-ipo.log 2>&1

# Jobs - Diariamente às 7:00 UTC
0 7 * * * cd $SOFIA_DIR && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# ============================================================================
# DATA COLLECTION - Python Collectors (NOVOS!)
# ============================================================================

# Global Data Collectors - Diariamente às 13:00 UTC (10:00 BRT)
0 13 * * * cd $SOFIA_DIR && ./run-all-with-venv.sh >> /var/log/sofia-python-collectors.log 2>&1

# ============================================================================
# ANALYTICS & EMAIL
# ============================================================================

# Run ALL: Análises + Email - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd $SOFIA_DIR && bash run-all-now.sh >> /var/log/sofia-pulse-complete.log 2>&1

# ============================================================================
# BACKUPS
# ============================================================================

# Auto-recovery
*/1 * * * * $USER_HOME/infraestrutura/scripts/auto-recovery.sh 2>/dev/null || true

# Backups diversos
0 3 * * * $USER_HOME/infraestrutura/scripts/comprehensive-backup.sh 2>/dev/null || true
0 2 * * * $USER_HOME/infraestrutura/scripts/backup-dashboards.sh 2>/dev/null || true
0 2 * * 3 $USER_HOME/infraestrutura/scripts/full-backup.sh 2>/dev/null || true

# Sofia backup
0 4 * * * cd $SOFIA_DIR && ./scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1 || true

# ============================================================================
# TOTAL: 19 Node collectors + 1 Python batch + 1 analytics + 5 backups = 26 jobs
# ============================================================================
CRONEOF

echo "✅ Novo crontab criado"
echo ""

echo "════════════════════════════════════════════════════════════════════════════════"
echo "📄 PREVIEW - NOVO CRONTAB:"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
cat /tmp/crontab-sofia-complete.txt | grep -v "^#" | grep -v "^$"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

echo "🔍 NOVIDADES:"
echo "   ✅ Python Collectors às 13:00 UTC (10:00 BRT):"
echo "      - Electricity Consumption (239 países)"
echo "      - Port Traffic (2,462 records)"
echo "      - Commodity Prices (5 commodities)"
echo "      - Semiconductor Sales (Q1 2025)"
echo ""
echo "   ✅ Analytics + Email às 22:00 UTC (19:00 BRT)"
echo "   ✅ Node.js collectors espalhados ao longo do dia"
echo "   ✅ Backups automáticos"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Aplicar este crontab? (y/n) " -n 1 -r
echo ""
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✅ Aplicando novo crontab..."
    crontab /tmp/crontab-sofia-complete.txt

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "✅ CRONTAB ATUALIZADO COM SUCESSO!"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "📅 Horários principais:"
    echo "   10:00 BRT (13:00 UTC) - Python Collectors"
    echo "   19:00 BRT (22:00 UTC) - Analytics + Email"
    echo ""
    echo "📊 Total de jobs: 26"
    echo "   - 19 Node.js collectors"
    echo "   - 1 Python batch (4 collectors)"
    echo "   - 1 Analytics + Email"
    echo "   - 5 Backups"
    echo ""
    echo "📝 Logs:"
    echo "   Python: /var/log/sofia-python-collectors.log"
    echo "   Analytics: /var/log/sofia-pulse-complete.log"
    echo ""
    echo "🔍 Comandos úteis:"
    echo "   crontab -l                               # Ver crontab"
    echo "   tail -f /var/log/sofia-python-collectors.log   # Ver logs Python"
    echo "   tail -f /var/log/sofia-pulse-complete.log      # Ver logs Analytics"
    echo ""

    if [ -n "$BACKUP_FILE" ]; then
        echo "💾 Backup salvo em: $BACKUP_FILE"
        echo "   Para restaurar: crontab $BACKUP_FILE"
        echo ""
    fi
else
    echo "❌ Cancelado"
    echo ""
    echo "Para aplicar manualmente:"
    echo "   crontab /tmp/crontab-sofia-complete.txt"
    echo ""
    if [ -n "$BACKUP_FILE" ]; then
        echo "Para restaurar backup:"
        echo "   crontab $BACKUP_FILE"
        echo ""
    fi
fi
