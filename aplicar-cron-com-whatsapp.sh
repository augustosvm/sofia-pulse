#!/bin/bash
################################################################################
# Aplicar crontab com notificações WhatsApp em TODOS os coletores
################################################################################

cd /home/ubuntu/sofia-pulse

# Tornar wrapper executável
chmod +x scripts/cron-wrapper.sh

# Criar crontab com wrapper
cat > ~/sofia-crontab-whatsapp.txt << 'EOF'
# ============================================================================
# SOFIA PULSE - CRONTAB COM WHATSAPP (55 COLLECTORS)
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SOFIA_DIR=/home/ubuntu/sofia-pulse

# Limpeza semanal
0 0 * * 1 cd $SOFIA_DIR && find analytics -name "*.txt" -mtime +30 -delete 2>/dev/null

# 06:00 UTC - Dados BR
0 6 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-bacen-sgs.py "BACEN SGS"
10 6 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-ibge-api.py "IBGE"
20 6 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-ipea-api.py "IPEA"
30 6 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-mdic-comexstat.py "ComexStat"

# 07:00 UTC - Energia
0 7 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-electricity-consumption.py "Eletricidade"
10 7 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-energy-global.py "Energia Global"
20 7 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-commodity-prices.py "Commodities"
30 7 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-semiconductor-sales.py "Semicondutores"
40 7 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-cardboard-production.ts "Papelão"

# 08:00 UTC - Tech
0 8 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-hackernews.ts "HackerNews"
15 8 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-npm-stats.ts "NPM Stats"
30 8 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-pypi-stats.ts "PyPI Stats"

# 09:00 UTC - Migrations
0 9 * * 1 cd $SOFIA_DIR && bash run-migration-nih-fix.sh >> /var/log/sofia/migrations.log 2>&1

# 10:00 UTC - GitHub
0 10 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-github-trending.ts "GitHub Trending"
30 10 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-github-niches.ts "GitHub Niches"

# 11:00 UTC - Research
0 11 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-arxiv-ai.ts "ArXiv AI"
15 11 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-openalex.ts "OpenAlex"
30 11 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-nih-grants.ts "NIH Grants"
45 11 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-asia-universities.ts "Universidades"

# 12:00 UTC - Orgs Int (1)
0 12 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-who-health.py "WHO"
15 12 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-unicef.py "UNICEF"
30 12 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-ilostat.py "ILO"
45 12 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-un-sdg.py "UN SDG"

# 13:00 UTC - Orgs Int (2) + VAGAS
0 13 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-hdx-humanitarian.py "HDX"
15 13 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-wto-trade.py "WTO"
30 13 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-fao-agriculture.py "FAO"
45 13 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-cepal-latam.py "CEPAL"
50 13 * * 1-5 cd $SOFIA_DIR && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-morning.log 2>&1

# 14:00 UTC - Women + HN
0 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-women-world-bank.py "Women World Bank"
0 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-hackernews.ts "HackerNews (2)"
10 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-women-eurostat.py "Women Eurostat"
20 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-women-fred.py "Women FRED"
30 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-women-ilostat.py "Women ILO"
40 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-women-brazil.py "Women Brasil"
50 14 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-central-banks-women.py "Bancos Centrais Women"

# 15:00 UTC - Social
0 15 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-religion-data.py "Religião"
15 15 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-world-ngos.py "ONGs"
30 15 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-drugs-data.py "Drogas"
45 15 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-world-security.py "Segurança Mundial"

# 16:00 UTC - Tourism
0 16 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-world-tourism.py "Turismo"
15 16 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-port-traffic.py "Portos"
30 16 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-socioeconomic-indicators.py "Socioeconômico"

# 17:00 UTC - Sports
0 17 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-sports-federations.py "Federações Esportivas"
20 17 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-sports-regional.py "Esportes Regionais"
40 17 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-world-sports.py "Esportes Mundial"

# 18:00 UTC - Brazil + VAGAS + HN
0 18 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-brazil-security.py "Segurança Brasil"
0 18 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-hackernews.ts "HackerNews (3)"
20 18 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-brazil-ministries.py "Ministérios Brasil"
30 18 * * 1-5 cd $SOFIA_DIR && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-afternoon.log 2>&1

# 19:00 UTC - Patents
0 19 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-epo-patents.ts "Patentes EPO"
20 19 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-wipo-china-patents.ts "Patentes WIPO"
40 19 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-ai-regulation.ts "Regulação IA"

# 20:00 UTC - Space
0 20 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-space-industry.ts "Indústria Espacial"
15 20 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-cybersecurity.ts "Cibersegurança"
30 20 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-gdelt.ts "GDELT"

# 21:00 UTC - Specialized + VAGAS
0 21 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-world-bank-gender.py "World Bank Gender"
15 21 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-basedosdados.py "Base dos Dados"
30 21 * * 1-5 $SOFIA_DIR/scripts/cron-wrapper.sh collect-ai-companies.ts "Empresas IA"
45 21 * * * $SOFIA_DIR/scripts/cron-wrapper.sh collect-hkex-ipos.ts "IPOs HKEX"
50 21 * * 1-5 cd $SOFIA_DIR && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-evening.log 2>&1

# 22:00 UTC - Analytics
0 22 * * 1-5 cd $SOFIA_DIR && bash run-mega-analytics-with-alerts.sh >> /var/log/sofia/analytics.log 2>&1

# 22:30 UTC - Email
30 22 * * 1-5 cd $SOFIA_DIR && bash send-email-mega.sh >> /var/log/sofia/email.log 2>&1
EOF

crontab ~/sofia-crontab-whatsapp.txt
echo "✅ Crontab com WhatsApp aplicado!"
crontab -l | grep -c "cron-wrapper"
