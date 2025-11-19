#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "🚀 FASE 2: Correlações e Dark Horses"
echo "=" | head -c 60
echo ""

source venv-analytics/bin/activate

# 1. Correlação Papers ↔ Funding
echo "🔗 1. Correlação Papers ↔ Funding..."
python3 analytics/correlation-papers-funding.py > analytics/correlation-latest.txt 2>&1
tail -50 analytics/correlation-latest.txt
echo ""

# 2. Dark Horses Report
echo "🐴 2. Dark Horses Report..."
python3 analytics/dark-horses-report.py
echo ""

# 3. Consolidar em relatório único
echo "📄 3. Consolidando relatório..."

cat > analytics/phase2-report.txt << 'EOF'
════════════════════════════════════════════════════════════════════════════════
                    SOFIA PULSE - PHASE 2 ANALYSIS
════════════════════════════════════════════════════════════════════════════════

EOF

date '+%Y-%m-%d %H:%M:%S UTC' >> analytics/phase2-report.txt
echo "" >> analytics/phase2-report.txt

echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/phase2-report.txt
echo "                    CORRELAÇÕES: PAPERS ↔ FUNDING" >> analytics/phase2-report.txt
echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/phase2-report.txt
echo "" >> analytics/phase2-report.txt

tail -n +5 analytics/correlation-latest.txt >> analytics/phase2-report.txt 2>/dev/null || true

echo "" >> analytics/phase2-report.txt
echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/phase2-report.txt
echo "                    DARK HORSES (OPORTUNIDADES)" >> analytics/phase2-report.txt
echo "════════════════════════════════════════════════════════════════════════════════" >> analytics/phase2-report.txt
echo "" >> analytics/phase2-report.txt

tail -n +5 analytics/dark-horses-latest.txt >> analytics/phase2-report.txt 2>/dev/null || true

echo ""
echo "✅ Relatório Fase 2: analytics/phase2-report.txt"
echo ""
head -100 analytics/phase2-report.txt
