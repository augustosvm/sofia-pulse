#!/bin/bash
# ============================================================================
# SOFIA PULSE - COMPLETE CRONTAB UPDATE
# ============================================================================
# Generated: 2026-01-14
# Total collectors: 70+ (all scheduled)
# ============================================================================

cat << 'CRONTAB_END' | crontab -

# ============================================================================
# SOFIA PULSE - COMPLETE DISTRIBUTED SCHEDULE (70+ COLLECTORS)
# ============================================================================
# Strategy:
# - Fast APIs: Multiple times per day (high frequency data)
# - Rate limited APIs: Spread throughout day (avoid rate limits)
# - Government data: Once daily (updated daily/weekly)
# - Research data: Once daily (updated weekly)
# - Jobs collectors: Spread to avoid rate limits
# - Analytics: Evening (after all collection done)
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SOFIA_DIR=/home/ubuntu/sofia-pulse

# ============================================================================
# 00:00 UTC (21:00 BRT) - CLEANUP & MAINTENANCE
# ============================================================================

# Weekly cleanup (Monday 00:00 UTC)
0 0 * * 1 cd $SOFIA_DIR && find analytics -name "*.txt" -mtime +30 -delete && find /var/log/sofia -name "*.log" -mtime +7 -delete 2>/dev/null

# ============================================================================
# 02:00 UTC (23:00 BRT) - SEC & BACKUPS
# ============================================================================

# SEC Edgar (IPOs, Form D)
0 2 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-sec-edgar-funding.py >> /var/log/sofia/sec-edgar.log 2>&1

# Backups
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-sofia-pulse.sh >> /var/log/sofia-pulse-backup.log 2>&1
0 3 * * * /home/ubuntu/infraestrutura/scripts/backup-sofia-mastra.sh >> /var/log/sofia-mastra-backup.log 2>&1
0 4 * * * /home/ubuntu/infraestrutura/scripts/backup-n8n.sh >> /var/log/n8n-backup.log 2>&1
0 5 * * 0 /home/ubuntu/infraestrutura/scripts/backup-monitoring.sh >> /var/log/monitoring-backup.log 2>&1

# ============================================================================
# 06:00 UTC (03:00 BRT) - BRAZIL OFFICIAL DATA
# ============================================================================

0 6 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-bacen-sgs.py >> /var/log/sofia/bacen.log 2>&1
10 6 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ibge-api.py >> /var/log/sofia/ibge.log 2>&1
20 6 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ipea-api.py >> /var/log/sofia/ipea.log 2>&1
30 6 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-mdic-comexstat.py >> /var/log/sofia/comexstat.log 2>&1
40 6 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-fiesp-data.py >> /var/log/sofia/fiesp.log 2>&1
50 6 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-cni-indicators.py >> /var/log/sofia/cni.log 2>&1

# ============================================================================
# 07:00 UTC (04:00 BRT) - ENERGY & COMMODITIES
# ============================================================================

0 7 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-electricity-consumption.py >> /var/log/sofia/electricity.log 2>&1
10 7 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-energy-global.py >> /var/log/sofia/energy-global.log 2>&1
20 7 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-commodity-prices.py >> /var/log/sofia/commodities.log 2>&1
30 7 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-semiconductor-sales.py >> /var/log/sofia/semiconductors.log 2>&1
40 7 * * * cd $SOFIA_DIR && npx tsx scripts/collect-cardboard-production.ts >> /var/log/sofia/cardboard.log 2>&1
50 7 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-currency-rates.ts >> /var/log/sofia/currency.log 2>&1

# ============================================================================
# 08:00 UTC (05:00 BRT) - TECH NEWS & COMMUNITY
# ============================================================================

0 8 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews.log 2>&1
15 8 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-npm-stats.ts >> /var/log/sofia/npm.log 2>&1
30 8 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-pypi-stats.ts >> /var/log/sofia/pypi.log 2>&1
45 8 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-reddit-tech.ts >> /var/log/sofia/reddit.log 2>&1

# ============================================================================
# 09:00 UTC (06:00 BRT) - AI/ML DATA SOURCES
# ============================================================================

0 9 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-ai-github-trends.ts >> /var/log/sofia/ai-github.log 2>&1
15 9 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-ai-npm-packages.ts >> /var/log/sofia/ai-npm.log 2>&1
30 9 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ai-pypi-packages.py >> /var/log/sofia/ai-pypi.log 2>&1
45 9 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ai-arxiv-keywords.py >> /var/log/sofia/ai-arxiv.log 2>&1

# Weekly migrations (Monday 09:00 UTC)
0 9 * * 1 cd $SOFIA_DIR && bash run-migration-nih-fix.sh >> /var/log/sofia/migrations.log 2>&1

# ============================================================================
# 09:30 UTC (06:30 BRT) - EDITORIAL INTELLIGENCE (StackExchange, Docker, PWC)
# ============================================================================

30 9 * * * cd $SOFIA_DIR && npx tsx scripts/run-all-intelligence.ts >> /var/log/sofia/intelligence.log 2>&1

# ============================================================================
# 10:00 UTC (07:00 BRT) - GITHUB (Rate Limited)
# ============================================================================

0 10 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-github-trending.ts >> /var/log/sofia/github-trending.log 2>&1
30 10 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-github-niches.ts >> /var/log/sofia/github-niches.log 2>&1

# YC Companies (Weekly Monday)
0 10 * * 1 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-yc-companies.py >> /var/log/sofia/yc-companies.log 2>&1

# ============================================================================
# 11:00 UTC (08:00 BRT) - RESEARCH & PAPERS
# ============================================================================

0 11 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-arxiv-ai.ts >> /var/log/sofia/arxiv.log 2>&1
15 11 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-openalex.ts >> /var/log/sofia/openalex.log 2>&1
30 11 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-nih-grants.ts >> /var/log/sofia/nih.log 2>&1
45 11 * * * cd $SOFIA_DIR && npx tsx scripts/collect-asia-universities.ts >> /var/log/sofia/asia-universities.log 2>&1

# Product Hunt (daily launches)
0 11 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-producthunt-api.py >> /var/log/sofia/producthunt.log 2>&1

# ============================================================================
# 12:00 UTC (09:00 BRT) - JOB COLLECTORS ORCHESTRATOR
# ============================================================================
# Runs all job collectors sequentially with timeouts and error handling
# Includes: Catho, InfoJobs, LinkedIn, Adzuna, Jooble, TheMuse, GitHub, USAJobs, etc.
0 12 * * * cd $SOFIA_DIR && npx tsx scripts/run-all-job-collectors.ts >> /var/log/sofia/jobs-orchestrator.log 2>&1

# ============================================================================
# 13:00 UTC (10:00 BRT) - TechCrunch & Funding
# ============================================================================

# TechCrunch Funding
0 13 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-techcrunch-funding.ts >> /var/log/sofia/techcrunch.log 2>&1

# AI HuggingFace
30 13 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ai-huggingface-models.py >> /var/log/sofia/huggingface.log 2>&1

# ============================================================================
# 14:00 UTC (11:00 BRT) - JOBS COLLECTORS (Part 3 - APIs)
# ============================================================================

0 14 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-himalayas-api.py >> /var/log/sofia/himalayas.log 2>&1
15 14 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-freejobs-api.py >> /var/log/sofia/freejobs.log 2>&1
30 14 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-careerjet-api.py >> /var/log/sofia/careerjet.log 2>&1
45 14 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-clinical-trials.py >> /var/log/sofia/clinical-trials.log 2>&1

# HackerNews 2nd run
0 14 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews-2.log 2>&1

# ============================================================================
# 15:00 UTC (12:00 BRT) - INTERNATIONAL ORGANIZATIONS (Part 1)
# ============================================================================

0 15 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-who-health.py >> /var/log/sofia/who.log 2>&1
15 15 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-unicef.py >> /var/log/sofia/unicef.log 2>&1
30 15 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-ilostat-labor.py >> /var/log/sofia/ilostat.log 2>&1
45 15 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-un-sdg.py >> /var/log/sofia/un-sdg.log 2>&1

# FDA Approvals
0 15 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-fda-approvals.py >> /var/log/sofia/fda.log 2>&1

# ============================================================================
# 16:00 UTC (13:00 BRT) - INTERNATIONAL ORGANIZATIONS (Part 2)
# ============================================================================

0 16 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-hdx-humanitarian.py >> /var/log/sofia/hdx.log 2>&1
15 16 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-wto-trade.py >> /var/log/sofia/wto.log 2>&1
30 16 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-fao-agriculture.py >> /var/log/sofia/fao.log 2>&1
45 16 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-cepal-latam.py >> /var/log/sofia/cepal.log 2>&1

# ============================================================================
# 17:00 UTC (14:00 BRT) - WOMEN & GENDER DATA
# ============================================================================

0 17 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-world-bank.py >> /var/log/sofia/women-wb.log 2>&1
10 17 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-eurostat.py >> /var/log/sofia/women-eurostat.log 2>&1
20 17 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-fred.py >> /var/log/sofia/women-fred.log 2>&1
30 17 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-ilostat.py >> /var/log/sofia/women-ilo.log 2>&1
40 17 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-women-brazil.py >> /var/log/sofia/women-brazil.log 2>&1
50 17 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-central-banks-women.py >> /var/log/sofia/central-banks-women.log 2>&1

# ============================================================================
# 18:00 UTC (15:00 BRT) - SOCIAL, SECURITY & DEMOGRAPHICS
# ============================================================================

0 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-religion-data.py >> /var/log/sofia/religion.log 2>&1
10 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-ngos.py >> /var/log/sofia/ngos.log 2>&1
20 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-drugs-data.py >> /var/log/sofia/drugs.log 2>&1
30 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-security.py >> /var/log/sofia/world-security.log 2>&1
40 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-brazil-security.py >> /var/log/sofia/brazil-security.log 2>&1
50 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-brazil-ministries.py >> /var/log/sofia/brazil-ministries.log 2>&1

# HackerNews 3rd run
0 18 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-hackernews.ts >> /var/log/sofia/hackernews-3.log 2>&1

# ACLED Conflicts
30 18 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-acled-conflicts.py >> /var/log/sofia/acled.log 2>&1

# ============================================================================
# 19:00 UTC (16:00 BRT) - TOURISM, TRADE & SOCIOECONOMIC
# ============================================================================

0 19 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-tourism.py >> /var/log/sofia/tourism.log 2>&1
15 19 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-port-traffic.py >> /var/log/sofia/ports.log 2>&1
30 19 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-socioeconomic-indicators.py >> /var/log/sofia/socioeconomic.log 2>&1
45 19 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-basedosdados-brazil.py >> /var/log/sofia/basedosdados.log 2>&1

# ============================================================================
# 20:00 UTC (17:00 BRT) - SPORTS DATA
# ============================================================================

0 20 * * * cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-sports-federations.py >> /var/log/sofia/sports-federations.log 2>&1
20 20 * * * cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-sports-regional.py >> /var/log/sofia/sports-regional.log 2>&1
40 20 * * * cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-sports.py >> /var/log/sofia/world-sports.log 2>&1

# ============================================================================
# 21:00 UTC (18:00 BRT) - PATENTS, CYBER, SPACE & EVENTS
# ============================================================================

0 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-epo-patents.ts >> /var/log/sofia/epo-patents.log 2>&1
10 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-wipo-china-patents.ts >> /var/log/sofia/wipo-patents.log 2>&1
20 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-ai-regulation.ts >> /var/log/sofia/ai-regulation.log 2>&1
30 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-space-industry.ts >> /var/log/sofia/space.log 2>&1
40 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-cybersecurity.ts >> /var/log/sofia/cybersecurity.log 2>&1
50 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-gdelt.ts >> /var/log/sofia/gdelt.log 2>&1

# GitGuardian Security
30 21 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-gitguardian-incidents.ts >> /var/log/sofia/gitguardian.log 2>&1

# ============================================================================
# 22:00 UTC (19:00 BRT) - SPECIALIZED & IPOs
# ============================================================================

0 22 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && python3 scripts/collect-world-bank-gender.py >> /var/log/sofia/wb-gender.log 2>&1
15 22 * * 1-5 cd $SOFIA_DIR && npx tsx scripts/collect-ai-companies.ts >> /var/log/sofia/ai-companies.log 2>&1
30 22 * * * cd $SOFIA_DIR && npx tsx scripts/collect-hkex-ipos.ts >> /var/log/sofia/hkex.log 2>&1

# ============================================================================
# 23:00 UTC (20:00 BRT) - ANALYTICS
# ============================================================================

0 23 * * 1-5 cd $SOFIA_DIR && bash run-mega-analytics-with-alerts.sh >> /var/log/sofia/analytics.log 2>&1

# ============================================================================
# 23:30 UTC (20:30 BRT) - EMAIL REPORT
# ============================================================================

30 23 * * 1-5 cd $SOFIA_DIR && python3 send-email-mega.py >> /var/log/sofia/email.log 2>&1

# ============================================================================
# NOTE: The following collectors require API keys or special setup:
# - collect-rapidapi-linkedin.py (RapidAPI key)
# - collect-rapidapi-activejobs.py (RapidAPI key)
# - collect-serpapi-googlejobs.py (SerpAPI key)
# - collect-theirstack-api.py (TheirStack API key)
# - collect-google-maps-locations.ts (Google Maps API key)
# - collect-rest-countries.ts (basic, can be enabled)
# - collect-vpic-vehicles.ts (NHTSA API - specific use case)
# - collect-research-papers.ts (duplicate of arxiv/openalex)
# - collect-focused-areas.py (internal use)
# ============================================================================

CRONTAB_END

echo "✅ Crontab updated with 70+ collectors!"
echo ""
echo "Summary of changes:"
echo "  - Added 15 jobs collectors (Catho, InfoJobs, GitHub Jobs, USAJobs, etc.)"
echo "  - Added 4 AI/ML collectors (AI GitHub, AI NPM, AI PyPI, AI ArXiv)"
echo "  - Added 3 Brazil collectors (FIESP, CNI, BaseDados Brazil)"
echo "  - Added security collectors (ACLED, GitGuardian)"
echo "  - Added currency rates collector"
echo "  - Moved analytics to 23:00 UTC (after all collection done)"
echo "  - Moved email to 23:30 UTC"
echo ""
echo "Collectors NOT scheduled (require API keys):"
echo "  - rapidapi-linkedin.py (RapidAPI)"
echo "  - rapidapi-activejobs.py (RapidAPI)"
echo "  - serpapi-googlejobs.py (SerpAPI)"
echo "  - theirstack-api.py (TheirStack)"
echo "  - google-maps-locations.ts (Google Maps)"
