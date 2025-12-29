#!/bin/bash
# Adicionar os 25 coletores faltantes ao crontab distribuído

# Backup do crontab atual
crontab -l > /tmp/crontab-before-adding-25.txt

# Criar arquivo temporário com crontab atual + novos coletores
crontab -l > /tmp/new-crontab-with-25.txt

# Adicionar os 25 coletores faltantes distribuídos ao longo do dia

cat >> /tmp/new-crontab-with-25.txt << 'EOF'

# ============================================================================
# NOVOS COLETORES ADICIONADOS (25 faltantes)
# ============================================================================

# 09:00 UTC - AI Data (5 coletores)
0 9 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-ai-arxiv-keywords.py >> /var/log/sofia/ai-arxiv-keywords.log 2>&1
10 9 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-ai-github-trends.ts >> /var/log/sofia/ai-github-trends.log 2>&1
20 9 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-ai-huggingface-models.py >> /var/log/sofia/ai-huggingface.log 2>&1
30 9 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-ai-npm-packages.ts >> /var/log/sofia/ai-npm.log 2>&1
40 9 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-ai-pypi-packages.py >> /var/log/sofia/ai-pypi.log 2>&1

# 13:00 UTC - Jobs APIs (11 coletores) - Parte 1
0 13 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-adzuna.ts >> /var/log/sofia/jobs-adzuna.log 2>&1
10 13 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-arbeitnow.ts >> /var/log/sofia/jobs-arbeitnow.log 2>&1
20 13 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-github.ts >> /var/log/sofia/jobs-github.log 2>&1
30 13 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-himalayas.ts >> /var/log/sofia/jobs-himalayas.log 2>&1
40 13 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-themuse.ts >> /var/log/sofia/jobs-themuse.log 2>&1
50 13 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-usajobs.ts >> /var/log/sofia/jobs-usajobs.log 2>&1

# 14:30 UTC - Jobs APIs (11 coletores) - Parte 2
0 14 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-jobs-weworkremotely.ts >> /var/log/sofia/jobs-wwr.log 2>&1
10 14 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-careerjet-api.py >> /var/log/sofia/jobs-careerjet.log 2>&1
20 14 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-freejobs-api.py >> /var/log/sofia/jobs-freejobs.log 2>&1
30 14 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-infojobs-brasil.py >> /var/log/sofia/jobs-infojobs.log 2>&1
40 14 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-serpapi-googlejobs.py >> /var/log/sofia/jobs-serpapi.log 2>&1

# 15:30 UTC - Funding & Startups (3 coletores)
0 15 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-sec-edgar-funding.py >> /var/log/sofia/sec-edgar.log 2>&1
15 15 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-yc-companies.py >> /var/log/sofia/yc-companies.log 2>&1
30 15 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-producthunt-api.py >> /var/log/sofia/producthunt.log 2>&1

# 16:30 UTC - RapidAPI & Others (6 coletores)
0 16 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-rapidapi-activejobs.py >> /var/log/sofia/rapidapi-activejobs.log 2>&1
10 16 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-rapidapi-linkedin.py >> /var/log/sofia/rapidapi-linkedin.log 2>&1
20 16 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-theirstack-api.py >> /var/log/sofia/theirstack.log 2>&1
30 16 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-himalayas-api.py >> /var/log/sofia/himalayas-api.log 2>&1
40 16 * * 1-5 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-reddit-tech.ts >> /var/log/sofia/reddit-tech.log 2>&1
50 16 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-focused-areas.py >> /var/log/sofia/focused-areas.log 2>&1

EOF

# Aplicar novo crontab
crontab /tmp/new-crontab-with-25.txt

echo "✅ Adicionados 25 coletores faltantes ao crontab!"
echo ""
echo "📊 RESUMO:"
echo "   Antes: 54 coletores"
echo "   Adicionados: 25 coletores"
echo "   Total agora: 79 coletores"
echo ""
echo "📅 DISTRIBUIÇÃO DOS NOVOS:"
echo "   09:00 UTC - AI Data (5)"
echo "   13:00 UTC - Jobs APIs Parte 1 (6)"
echo "   14:00 UTC - Jobs APIs Parte 2 (5)"
echo "   15:00 UTC - Funding & Startups (3)"
echo "   16:00 UTC - RapidAPI & Others (6)"
echo ""
echo "📝 Verificar:"
echo "   crontab -l | grep -c 'collect-'"
echo ""
echo "📋 Backup salvo em:"
echo "   /tmp/crontab-before-adding-25.txt"
