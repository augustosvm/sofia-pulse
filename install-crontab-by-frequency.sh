#!/bin/bash
################################################################################
# Sofia Pulse - Install Crontab by Frequency (ALL 55 Collectors)
# Grouped by how often data updates (daily, weekly, monthly)
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📅 INSTALLING CRONTAB BY FREQUENCY (ALL 55 COLLECTORS)"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we're on the server (not WSL)
if [[ "$PWD" == /mnt/c/* ]]; then
    echo "⚠️  WARNING: You're on Windows/WSL!"
    echo "   Run on server: ssh ubuntu@SERVER && cd /home/ubuntu/sofia-pulse"
    exit 1
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
find scripts -name "collect-*.py" -exec chmod +x {} \; 2>/dev/null || true
find scripts -name "collect-*.ts" -exec chmod +x {} \; 2>/dev/null || true
chmod +x run-mega-analytics-with-alerts.sh send-email-mega.sh run-migration-nih-fix.sh 2>/dev/null || true
echo ""

# Backup current crontab
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"
echo "📋 Backup: $BACKUP_FILE"
echo ""

SOFIA_DIR="$PWD"

# Create frequency-based crontab
cat > /tmp/sofia-crontab-frequency.txt << 'CRONTAB_END'
# ============================================================================
# SOFIA PULSE - FREQUENCY-BASED SCHEDULE (ALL 55 COLLECTORS)
# ============================================================================
# Strategy: Group collectors by data update frequency
# - HOURLY: News, community data (updated constantly)
# - DAILY: APIs, markets, most data sources
# - WEEKLY: Research, universities, sports rankings
# - MONTHLY: Demographics, structural data
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ============================================================================
# HOURLY - High Frequency Data (8 collectors)
# Data updates: Every few minutes to hours
# Run: Every 3 hours during business hours
# ============================================================================

# Tech News & Community (3 collectors)
0 8,11,14,17,20 * * 1-5 cd $(pwd) && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews.log 2>&1
10 8,11,14,17,20 * * 1-5 cd $(pwd) && npx tsx scripts/collect-reddit-tech.ts >> /var/log/sofia/reddit.log 2>&1

# Package Stats (2 collectors)
20 8,11,14,17,20 * * 1-5 cd $(pwd) && npx tsx scripts/collect-npm-stats.ts >> /var/log/sofia/npm.log 2>&1
30 8,11,14,17,20 * * 1-5 cd $(pwd) && npx tsx scripts/collect-pypi-stats.ts >> /var/log/sofia/pypi.log 2>&1

# GitHub Trending (2 collectors) - Rate limited to 3x/day
0 10,14,18 * * 1-5 cd $(pwd) && npx tsx scripts/collect-github-trending.ts >> /var/log/sofia/github-trending.log 2>&1
30 10,14,18 * * 1-5 cd $(pwd) && npx tsx scripts/collect-github-niches.ts >> /var/log/sofia/github-niches.log 2>&1

# Events & News (1 collector)
0 9,13,17,21 * * 1-5 cd $(pwd) && npx tsx scripts/collect-gdelt.ts >> /var/log/sofia/gdelt.log 2>&1

# ============================================================================
# DAILY - Standard Frequency (34 collectors)
# Data updates: Once per day
# Run: Once daily at 10:00 UTC (07:00 BRT)
# ============================================================================

# --- Brazil Official Data (6 collectors) - Updates daily ---
0 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-bacen-sgs.py >> /var/log/sofia/bacen.log 2>&1
5 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-ibge-api.py >> /var/log/sofia/ibge.log 2>&1
10 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-ipea-api.py >> /var/log/sofia/ipea.log 2>&1
15 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-mdic-comexstat.py >> /var/log/sofia/comexstat.log 2>&1
20 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-brazil-ministries.py >> /var/log/sofia/brazil-ministries.log 2>&1
25 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-brazil-security.py >> /var/log/sofia/brazil-security.log 2>&1

# --- Energy & Commodities (4 collectors) - Updates daily ---
30 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-electricity-consumption.py >> /var/log/sofia/electricity.log 2>&1
35 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-energy-global.py >> /var/log/sofia/energy-global.log 2>&1
40 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-commodity-prices.py >> /var/log/sofia/commodities.log 2>&1
45 10 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-port-traffic.py >> /var/log/sofia/ports.log 2>&1

# --- Research & Academia (4 collectors) - Updates daily ---
50 10 * * 1-5 cd $(pwd) && npx tsx scripts/collect-arxiv-ai.ts >> /var/log/sofia/arxiv.log 2>&1
55 10 * * 1-5 cd $(pwd) && npx tsx scripts/collect-openalex.ts >> /var/log/sofia/openalex.log 2>&1
0 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-nih-grants.ts >> /var/log/sofia/nih.log 2>&1

# --- Patents & IP (4 collectors) - Updates daily ---
5 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-epo-patents.ts >> /var/log/sofia/epo.log 2>&1
10 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-wipo-china-patents.ts >> /var/log/sofia/wipo.log 2>&1
15 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-ai-regulation.ts >> /var/log/sofia/ai-regulation.log 2>&1
20 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-ai-companies.ts >> /var/log/sofia/ai-companies.log 2>&1

# --- Cybersecurity & Space (2 collectors) - Updates daily ---
25 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-cybersecurity.ts >> /var/log/sofia/cybersecurity.log 2>&1
30 11 * * 1-5 cd $(pwd) && npx tsx scripts/collect-space-industry.ts >> /var/log/sofia/space.log 2>&1

# --- International Organizations (8 collectors) - Updates daily ---
35 11 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-who-health.py >> /var/log/sofia/who.log 2>&1
40 11 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-unicef.py >> /var/log/sofia/unicef.log 2>&1
45 11 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-ilostat.py >> /var/log/sofia/ilo.log 2>&1
50 11 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-un-sdg.py >> /var/log/sofia/un-sdg.log 2>&1
55 11 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-hdx-humanitarian.py >> /var/log/sofia/hdx.log 2>&1
0 12 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-wto-trade.py >> /var/log/sofia/wto.log 2>&1
5 12 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-fao-agriculture.py >> /var/log/sofia/fao.log 2>&1
10 12 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-cepal-latam.py >> /var/log/sofia/cepal.log 2>&1

# --- Tourism & Trade (2 collectors) - Updates daily ---
15 12 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-world-tourism.py >> /var/log/sofia/tourism.log 2>&1
20 12 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-world-security.py >> /var/log/sofia/world-security.log 2>&1

# --- Manufacturing (2 collectors) - Updates daily ---
25 12 * * 1-5 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-semiconductor-sales.py >> /var/log/sofia/semiconductors.log 2>&1
30 12 * * 1-5 cd $(pwd) && npx tsx scripts/collect-cardboard-production.ts >> /var/log/sofia/cardboard.log 2>&1

# --- IPOs (1 collector) - Updates daily ---
35 12 * * 1-5 cd $(pwd) && npx tsx scripts/collect-hkex-ipos.ts >> /var/log/sofia/hkex.log 2>&1

# ============================================================================
# WEEKLY - Low Frequency Data (10 collectors)
# Data updates: Weekly or less often
# Run: Monday only at 13:00 UTC (10:00 BRT)
# ============================================================================

# --- Women & Gender Data (6 collectors) - Updates weekly/monthly ---
0 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-women-world-bank.py >> /var/log/sofia/women-wb.log 2>&1
5 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-women-eurostat.py >> /var/log/sofia/women-eurostat.log 2>&1
10 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-women-fred.py >> /var/log/sofia/women-fred.log 2>&1
15 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-women-ilostat.py >> /var/log/sofia/women-ilo.log 2>&1
20 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-women-brazil.py >> /var/log/sofia/women-brazil.log 2>&1
25 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-central-banks-women.py >> /var/log/sofia/central-banks-women.log 2>&1

# --- Sports Rankings (3 collectors) - Updates weekly ---
30 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-sports-federations.py >> /var/log/sofia/sports-federations.log 2>&1
35 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-sports-regional.py >> /var/log/sofia/sports-regional.log 2>&1
40 13 * * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-world-sports.py >> /var/log/sofia/world-sports.log 2>&1

# --- Universities (1 collector) - Updates weekly ---
45 13 * * 1 cd $(pwd) && npx tsx scripts/collect-asia-universities.ts >> /var/log/sofia/asia-universities.log 2>&1

# ============================================================================
# MONTHLY - Very Low Frequency (3 collectors)
# Data updates: Monthly or rarely
# Run: 1st Monday of month at 14:00 UTC (11:00 BRT)
# ============================================================================

# --- Demographics & Social (3 collectors) - Updates monthly/rarely ---
0 14 1-7 * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-socioeconomic-indicators.py >> /var/log/sofia/socioeconomic.log 2>&1
10 14 1-7 * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-religion-data.py >> /var/log/sofia/religion.log 2>&1
20 14 1-7 * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-world-ngos.py >> /var/log/sofia/ngos.log 2>&1
30 14 1-7 * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-drugs-data.py >> /var/log/sofia/drugs.log 2>&1
40 14 1-7 * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-world-bank-gender.py >> /var/log/sofia/wb-gender.log 2>&1
50 14 1-7 * 1 cd $(pwd) && source venv-analytics/bin/activate && python3 scripts/collect-basedosdados.py >> /var/log/sofia/basedosdados.log 2>&1

# ============================================================================
# ANALYTICS & REPORTS
# Run: Daily at 22:00 UTC (19:00 BRT) after all collection
# ============================================================================

0 22 * * 1-5 cd $(pwd) && bash run-mega-analytics-with-alerts.sh >> /var/log/sofia/analytics.log 2>&1
30 22 * * 1-5 cd $(pwd) && bash send-email-mega.sh >> /var/log/sofia/email.log 2>&1

# ============================================================================
# MAINTENANCE
# ============================================================================

# Database migrations (Monday 09:00 UTC)
0 9 * * 1 cd $(pwd) && bash run-migration-nih-fix.sh >> /var/log/sofia/migrations.log 2>&1

# Cleanup old files (Sunday 02:00 UTC)
0 2 * * 0 cd $(pwd) && find analytics -name "*.txt" -mtime +30 -delete && find /var/log/sofia -name "*.log" -mtime +7 -delete 2>/dev/null

CRONTAB_END

# Replace $(pwd) with actual directory
sed "s|\$(pwd)|$SOFIA_DIR|g" /tmp/sofia-crontab-frequency.txt > /tmp/sofia-crontab-final.txt

echo "════════════════════════════════════════════════════════════════"
echo "📄 FREQUENCY-BASED CRONTAB (ALL 55 COLLECTORS)"
echo "════════════════════════════════════════════════════════════════"
cat /tmp/sofia-crontab-final.txt
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Apply crontab
crontab /tmp/sofia-crontab-final.txt

echo "✅ Frequency-based crontab installed!"
echo ""
echo "📊 SUMMARY BY FREQUENCY:"
echo ""
echo "🔄 HOURLY (8 collectors) - Every 3 hours during business hours"
echo "   • HackerNews, Reddit (news)"
echo "   • NPM, PyPI (packages)"
echo "   • GitHub Trending, Niches (repositories)"
echo "   • GDELT (events)"
echo ""
echo "📅 DAILY (34 collectors) - Once per day at 10:00-12:00 UTC"
echo "   • Brazil: BACEN, IBGE, IPEA, ComexStat, Ministries, Security (6)"
echo "   • Energy & Commodities: Electricity, Energy, Prices, Ports (4)"
echo "   • Research: ArXiv, OpenAlex, NIH (3)"
echo "   • Patents: EPO, WIPO, AI Regulation, AI Companies (4)"
echo "   • Security: Cybersecurity, Space (2)"
echo "   • International: WHO, UNICEF, ILO, UN, HDX, WTO, FAO, CEPAL (8)"
echo "   • Tourism & Trade: Tourism, Security (2)"
echo "   • Manufacturing: Semiconductors, Cardboard (2)"
echo "   • IPOs: Hong Kong (1)"
echo ""
echo "📆 WEEKLY (10 collectors) - Mondays only at 13:00 UTC"
echo "   • Women/Gender: World Bank, Eurostat, FRED, ILO, Brazil, Central Banks (6)"
echo "   • Sports: Federations, Regional, World Sports (3)"
echo "   • Universities: Asia Universities (1)"
echo ""
echo "📌 MONTHLY (6 collectors) - 1st Monday at 14:00 UTC"
echo "   • Demographics: Socioeconomic Indicators, Religion, NGOs (3)"
echo "   • Drugs, Gender focus, BasedosDados (3)"
echo ""
echo "📈 ANALYTICS - Daily at 22:00 UTC (19:00 BRT)"
echo "   • 33 reports generated"
echo "   • Email sent at 22:30 UTC"
echo ""
echo "📝 VERIFY INSTALLATION:"
echo "   crontab -l | grep -c 'collect-'"
echo "   # Should show 55 collector jobs"
echo ""
echo "🧪 TEST INDIVIDUAL COLLECTOR:"
echo "   cd $SOFIA_DIR"
echo "   source venv-analytics/bin/activate"
echo "   python3 scripts/collect-bacen-sgs.py"
echo ""
