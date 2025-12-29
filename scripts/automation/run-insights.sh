#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "🔥 Coletando dados REAIS..."

# Coletar dados reais
npm run collect:github-trending 2>&1 | grep -E "(✅|❌|Fetched)" || true
sleep 2
npm run collect:hackernews 2>&1 | grep -E "(✅|❌|Fetched)" || true
sleep 2
npm run collect:gdelt 2>&1 | grep -E "(✅|❌|Fetched)" || true

echo ""
echo "🧮 Gerando Tech Trend Score..."

source venv-analytics/bin/activate
python3 analytics/tech-trend-score-simple.py > analytics/tech-trends/latest.txt 2>&1

echo ""
echo "🔗 Gerando Correlações Papers ↔ Funding..."
python3 analytics/correlation-papers-funding.py > analytics/correlation-latest.txt 2>&1

echo ""
echo "🐴 Gerando Dark Horses Report..."
python3 analytics/dark-horses-report.py > /dev/null 2>&1

echo ""
echo "📊 Gerando Premium Insights v2.0..."

if [ -f "generate-insights-v2.0.sh" ]; then
    bash generate-insights-v2.0.sh 2>&1 | tail -50
fi

echo ""
echo "📄 Consolidando..."

cat > analytics/sofia-report.txt << 'EOF'
════════════════════════════════════════════════════════════════════════════════
                    🤖 SOFIA PULSE - INTELLIGENCE REPORT
════════════════════════════════════════════════════════════════════════════════
EOF

date '+%Y-%m-%d %H:%M:%S UTC' >> analytics/sofia-report.txt
echo "" >> analytics/sofia-report.txt

cat analytics/tech-trends/latest.txt >> analytics/sofia-report.txt 2>/dev/null || true
echo "" >> analytics/sofia-report.txt

echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/sofia-report.txt
echo "                    CORRELAÇÕES: PAPERS ↔ FUNDING" >> analytics/sofia-report.txt
echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/sofia-report.txt
echo "" >> analytics/sofia-report.txt
tail -n +5 analytics/correlation-latest.txt >> analytics/sofia-report.txt 2>/dev/null || true
echo "" >> analytics/sofia-report.txt

echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/sofia-report.txt
echo "                    DARK HORSES (OPORTUNIDADES)" >> analytics/sofia-report.txt
echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/sofia-report.txt
echo "" >> analytics/sofia-report.txt
cat analytics/dark-horses-latest.txt >> analytics/sofia-report.txt 2>/dev/null || true
echo "" >> analytics/sofia-report.txt

if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
    tail -n +5 analytics/premium-insights/latest-geo.txt >> analytics/sofia-report.txt
fi

echo ""
echo "✅ Pronto: analytics/sofia-report.txt"
echo ""
head -100 analytics/sofia-report.txt
