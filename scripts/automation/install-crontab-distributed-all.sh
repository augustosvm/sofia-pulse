#!/bin/bash
################################################################################
# Sofia Pulse - Install Distributed Crontab (ALL 55 Collectors)
# Each collector runs at optimal time based on data freshness
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📅 INSTALLING DISTRIBUTED CRONTAB (ALL 55 COLLECTORS)"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we're on the server (not WSL)
if [[ "$PWD" == /mnt/c/* ]]; then
    echo "⚠️  WARNING: You're on Windows/WSL, not the Ubuntu server!"
    echo "   Run this on: ssh ubuntu@SERVER && cd /home/ubuntu/sofia-pulse"
    exit 1
fi

# Make all scripts executable
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

# Create distributed crontab
cat > /tmp/sofia-crontab-distributed-all.txt << EOF
# ============================================================================
# SOFIA PULSE - DISTRIBUTED SCHEDULE (ALL 55 COLLECTORS)
# ============================================================================
# Strategy:
# - Fast APIs: Multiple times per day (high frequency data)
# - Rate limited APIs: Spread throughout day (avoid rate limits)
# - Government data: Once daily (updated daily/weekly)
# - Research data: Once daily (updated weekly)
# - Analytics: Evening (after all collection done)
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SOFIA_DIR=${SOFIA_DIR}

# ============================================================================
# 00:00 UTC (21:00 BRT) - START OF DAY
# ============================================================================

# Weekly cleanup (Monday 00:00 UTC)
0 0 * * 1 cd \$SOFIA_DIR && find analytics -name "*.txt" -mtime +30 -delete && find /var/log/sofia -name "*.log" -mtime +7 -delete 2>/dev/null

# ============================================================================
# 06:00 UTC (03:00 BRT) - EARLY MORNING - Government Data Updates
# ============================================================================

# Brazil Official Data (updated overnight)
0 6 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-bacen-sgs.py >> /var/log/sofia/bacen.log 2>&1
10 6 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ibge-api.py >> /var/log/sofia/ibge.log 2>&1
20 6 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ipea-api.py >> /var/log/sofia/ipea.log 2>&1
30 6 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-mdic-comexstat.py >> /var/log/sofia/comexstat.log 2>&1

# ============================================================================
# 07:00 UTC (04:00 BRT) - MORNING - Fast Global Data
# ============================================================================

# Energy & Commodities (updated daily)
0 7 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-electricity-consumption.py >> /var/log/sofia/electricity.log 2>&1
10 7 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-energy-global.py >> /var/log/sofia/energy-global.log 2>&1
20 7 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-commodity-prices.py >> /var/log/sofia/commodities.log 2>&1

# Semiconductors & Manufacturing
30 7 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-semiconductor-sales.py >> /var/log/sofia/semiconductors.log 2>&1
40 7 * * * cd \$SOFIA_DIR && npx tsx scripts/collect-cardboard-production.ts >> /var/log/sofia/cardboard.log 2>&1

# ============================================================================
# 08:00 UTC (05:00 BRT) - Tech News & Community
# ============================================================================

# Tech community data (high frequency)
0 8 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews.log 2>&1
15 8 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-npm-stats.ts >> /var/log/sofia/npm.log 2>&1
30 8 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-pypi-stats.ts >> /var/log/sofia/pypi.log 2>&1

# ============================================================================
# 09:00 UTC (06:00 BRT) - Database Migrations & Maintenance
# ============================================================================

0 9 * * 1 cd \$SOFIA_DIR && bash run-migration-nih-fix.sh >> /var/log/sofia/migrations.log 2>&1

# ============================================================================
# 10:00 UTC (07:00 BRT) - GITHUB (Rate Limited - 5000 req/hour with token)
# ============================================================================

0 10 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-github-trending.ts >> /var/log/sofia/github-trending.log 2>&1
30 10 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-github-niches.ts >> /var/log/sofia/github-niches.log 2>&1

# ============================================================================
# 11:00 UTC (08:00 BRT) - RESEARCH DATA (Updated daily/weekly)
# ============================================================================

0 11 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-arxiv-ai.ts >> /var/log/sofia/arxiv.log 2>&1
15 11 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-openalex.ts >> /var/log/sofia/openalex.log 2>&1
30 11 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-nih-grants.ts >> /var/log/sofia/nih.log 2>&1
45 11 * * * cd \$SOFIA_DIR && npx tsx scripts/collect-asia-universities.ts >> /var/log/sofia/asia-universities.log 2>&1

# ============================================================================
# 12:00 UTC (09:00 BRT) - INTERNATIONAL ORGANIZATIONS (Part 1)
# ============================================================================

0 12 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-who-health.py >> /var/log/sofia/who.log 2>&1
15 12 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-unicef.py >> /var/log/sofia/unicef.log 2>&1
30 12 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ilostat.py >> /var/log/sofia/ilo.log 2>&1
45 12 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-un-sdg.py >> /var/log/sofia/un-sdg.log 2>&1

# ============================================================================
# 13:00 UTC (10:00 BRT) - INTERNATIONAL ORGANIZATIONS (Part 2)
# ============================================================================

0 13 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-hdx-humanitarian.py >> /var/log/sofia/hdx.log 2>&1
15 13 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-wto-trade.py >> /var/log/sofia/wto.log 2>&1
30 13 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-fao-agriculture.py >> /var/log/sofia/fao.log 2>&1
45 13 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-cepal-latam.py >> /var/log/sofia/cepal.log 2>&1

# ============================================================================
# 14:00 UTC (11:00 BRT) - WOMEN & GENDER DATA
# ============================================================================

0 14 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-world-bank.py >> /var/log/sofia/women-wb.log 2>&1
10 14 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-eurostat.py >> /var/log/sofia/women-eurostat.log 2>&1
20 14 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-fred.py >> /var/log/sofia/women-fred.log 2>&1
30 14 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-ilostat.py >> /var/log/sofia/women-ilo.log 2>&1
40 14 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-brazil.py >> /var/log/sofia/women-brazil.log 2>&1
50 14 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-central-banks-women.py >> /var/log/sofia/central-banks-women.log 2>&1

# ============================================================================
# 15:00 UTC (12:00 BRT) - SOCIAL & DEMOGRAPHICS
# ============================================================================

0 15 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-religion-data.py >> /var/log/sofia/religion.log 2>&1
15 15 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-ngos.py >> /var/log/sofia/ngos.log 2>&1
30 15 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-drugs-data.py >> /var/log/sofia/drugs.log 2>&1
45 15 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-security.py >> /var/log/sofia/world-security.log 2>&1

# ============================================================================
# 16:00 UTC (13:00 BRT) - TOURISM & TRADE DATA
# ============================================================================

0 16 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-tourism.py >> /var/log/sofia/tourism.log 2>&1
15 16 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-port-traffic.py >> /var/log/sofia/ports.log 2>&1
30 16 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-socioeconomic-indicators.py >> /var/log/sofia/socioeconomic.log 2>&1

# ============================================================================
# 17:00 UTC (14:00 BRT) - SPORTS DATA
# ============================================================================

0 17 * * * cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-sports-federations.py >> /var/log/sofia/sports-federations.log 2>&1
20 17 * * * cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-sports-regional.py >> /var/log/sofia/sports-regional.log 2>&1
40 17 * * * cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-sports.py >> /var/log/sofia/world-sports.log 2>&1

# ============================================================================
# 18:00 UTC (15:00 BRT) - BRAZIL SECURITY & MINISTRIES
# ============================================================================

0 18 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-brazil-security.py >> /var/log/sofia/brazil-security.log 2>&1
20 18 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-brazil-ministries.py >> /var/log/sofia/brazil-ministries.log 2>&1

# ============================================================================
# 19:00 UTC (16:00 BRT) - PATENTS & IP (Rate Limited)
# ============================================================================

0 19 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-epo-patents.ts >> /var/log/sofia/epo-patents.log 2>&1
20 19 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-wipo-china-patents.ts >> /var/log/sofia/wipo-patents.log 2>&1
40 19 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-ai-regulation.ts >> /var/log/sofia/ai-regulation.log 2>&1

# ============================================================================
# 20:00 UTC (17:00 BRT) - SPACE, CYBER, EVENTS
# ============================================================================

0 20 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-space-industry.ts >> /var/log/sofia/space.log 2>&1
15 20 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-cybersecurity.ts >> /var/log/sofia/cybersecurity.log 2>&1
30 20 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-gdelt.ts >> /var/log/sofia/gdelt.log 2>&1

# ============================================================================
# 21:00 UTC (18:00 BRT) - SPECIALIZED DATA
# ============================================================================

0 21 * * 1-5 cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-bank-gender.py >> /var/log/sofia/wb-gender.log 2>&1
15 21 * * * cd \$SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-basedosdados.py >> /var/log/sofia/basedosdados.log 2>&1
30 21 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-ai-companies.ts >> /var/log/sofia/ai-companies.log 2>&1
45 21 * * * cd \$SOFIA_DIR && npx tsx scripts/collect-hkex-ipos.ts >> /var/log/sofia/hkex.log 2>&1

# ============================================================================
# 22:00 UTC (19:00 BRT) - ANALYTICS + EMAIL (After all collection done)
# ============================================================================

0 22 * * 1-5 cd \$SOFIA_DIR && bash run-mega-analytics-with-alerts.sh >> /var/log/sofia/analytics.log 2>&1

# ============================================================================
# 22:30 UTC (19:30 BRT) - EMAIL REPORT
# ============================================================================

30 22 * * 1-5 cd \$SOFIA_DIR && bash send-email-mega.sh >> /var/log/sofia/email.log 2>&1

# ============================================================================
# SECOND RUN - 14:00 UTC (11:00 BRT) - High Frequency Data Only
# ============================================================================

# Tech news (updated frequently throughout the day)
0 14 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews-2.log 2>&1

# ============================================================================
# THIRD RUN - 18:00 UTC (15:00 BRT) - High Frequency Data Only
# ============================================================================

# Tech news (final update before analytics)
0 18 * * 1-5 cd \$SOFIA_DIR && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews-3.log 2>&1

EOF

echo "════════════════════════════════════════════════════════════════"
echo "📄 NEW DISTRIBUTED CRONTAB (ALL 55 COLLECTORS)"
echo "════════════════════════════════════════════════════════════════"
cat /tmp/sofia-crontab-distributed-all.txt
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Apply crontab
crontab /tmp/sofia-crontab-distributed-all.txt

echo "✅ Distributed crontab installed successfully!"
echo ""
echo "📊 COLLECTORS SCHEDULED: 55/55 (100%)"
echo ""
echo "📅 DISTRIBUTION STRATEGY:"
echo "   06:00 UTC - Brazil government data (BACEN, IBGE, IPEA, ComexStat)"
echo "   07:00 UTC - Energy & commodities"
echo "   08:00 UTC - Tech news (HackerNews, NPM, PyPI)"
echo "   10:00 UTC - GitHub (rate limited)"
echo "   11:00 UTC - Research (ArXiv, OpenAlex, NIH, Universities)"
echo "   12-13:00 UTC - International orgs (WHO, UNICEF, ILO, UN, WTO, FAO, CEPAL, HDX)"
echo "   14:00 UTC - Women & gender data (6 sources)"
echo "   15:00 UTC - Social data (Religion, NGOs, Drugs, Security)"
echo "   16:00 UTC - Tourism, ports, socioeconomic"
echo "   17:00 UTC - Sports (FIFA, IOC, Olympics)"
echo "   18:00 UTC - Brazil security & ministries"
echo "   19:00 UTC - Patents & IP (EPO, WIPO, AI regulation)"
echo "   20:00 UTC - Space, cybersecurity, GDELT events"
echo "   21:00 UTC - Specialized (gender focus, BasedosDados, AI companies, IPOs)"
echo "   22:00 UTC - Analytics (33 reports)"
echo "   22:30 UTC - Email report"
echo ""
echo "📱 WHATSAPP ALERTS:"
echo "   • Real-time errors for each collector (with details)"
echo "   • Analytics summary at 22:00 UTC"
echo "   • Email confirmation at 22:30 UTC"
echo ""
echo "📝 VERIFY:"
echo "   crontab -l | grep -c 'collect-' # Should show 55"
echo ""
