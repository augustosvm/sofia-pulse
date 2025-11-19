#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - EXECUTAR TUDO AGORA"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

# 0. Executar migrations
echo "🗄️  0. Executando migrations do banco..."
bash run-migrations.sh 2>&1 | tail -10
echo ""

# 1. Corrigir DB configs
echo "🔧 1. Corrigindo configurações de DB..."
bash fix-all-db-configs.sh
echo ""

# 2. Coletar dados
echo "🔥 2. Coletando TODOS os dados..."
echo ""

source venv-analytics/bin/activate

npm run collect:reddit 2>&1 | tail -5 || true
sleep 2
npm run collect:npm-stats 2>&1 | tail -5 || true
sleep 2
npm run collect:pypi-stats 2>&1 | tail -5 || true
sleep 2

echo "🔒 Coletando Cybersecurity..."
npm run collect:cybersecurity 2>&1 | tail -5 || true
sleep 2

echo "🚀 Coletando Space Industry..."
npm run collect:space-industry 2>&1 | tail -5 || true
sleep 2

echo "⚖️  Coletando AI Regulation..."
npm run collect:ai-regulation 2>&1 | tail -5 || true
sleep 2

echo "🌍 Coletando GDELT Events..."
npm run collect:gdelt 2>&1 | tail -5 || true
sleep 2

echo ""
echo "📊 3. Gerando TODAS as análises..."
echo ""

python3 analytics/correlation-papers-funding.py > analytics/correlation-latest.txt 2>&1 && echo "   ✅ Correlações" || echo "   ⚠️  Correlações falhou"

python3 analytics/dark-horses-report.py 2>&1 | tail -5 && echo "   ✅ Dark Horses" || echo "   ⚠️  Dark Horses falhou"

python3 analytics/top10-tech-trends.py > analytics/top10-latest.txt 2>&1 && echo "   ✅ Top 10 Trends" || echo "   ⚠️  Top 10 falhou"

python3 analytics/entity-resolution.py > analytics/entity-resolution-latest.txt 2>&1 && echo "   ✅ Entity Resolution" || echo "   ⚠️  Entity Resolution falhou"

python3 analytics/nlg-playbooks-gemini.py 2>&1 | tail -5 && echo "   ✅ NLG Playbooks" || echo "   ⚠️  NLG falhou"

python3 analytics/special_sectors_analysis.py 2>&1 | tail -10 && echo "   ✅ Special Sectors Analysis" || echo "   ⚠️  Special Sectors falhou"

bash run-insights.sh 2>&1 | tail -10 && echo "   ✅ Insights consolidados" || echo "   ⚠️  Insights falhou"

echo ""
echo "📧 4. Enviando email..."
echo ""

bash send-email-all.sh

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ TUDO EXECUTADO E ENVIADO!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📧 Email enviado para: augustosvm@gmail.com"
echo ""
echo "📊 Relatórios:"
echo "   - analytics/sofia-report.txt (completo)"
echo "   - analytics/top10-latest.txt"
echo "   - analytics/correlation-latest.txt"
echo "   - analytics/dark-horses-latest.txt"
echo "   - analytics/entity-resolution-latest.txt"
echo "   - analytics/playbook-latest.txt"
echo "   - analytics/special-sectors-latest.txt (NEW!)"
echo ""
echo "✅ Pronto!"
echo ""
