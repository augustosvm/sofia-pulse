#!/bin/bash

################################################################################
# SOFIA PULSE - INTELLIGENCE ANALYTICS
# Roda as 6 análises preditivas
################################################################################

set -e

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

echo "════════════════════════════════════════════════════════════════"
echo "🧠 SOFIA PULSE - INTELLIGENCE ANALYTICS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Tempo estimado: 3-5 minutos"
echo "📈 Gerará 6 análises preditivas"
echo ""

# Activate virtual environment
source venv-analytics/bin/activate

echo "════════════════════════════════════════════════════════════════"
echo "🔮 PREDICTIVE INTELLIGENCE"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Career Trends Predictor (before companies hire)"
python3 analytics/career-trends-predictor.py || echo "⚠️  Skipped"
echo ""

echo "2️⃣  Capital Flow Predictor (before VCs invest)"
python3 analytics/capital-flow-predictor.py || echo "⚠️  Skipped"
echo ""

echo "3️⃣  Expansion Location Analyzer (strategic expansion)"
python3 analytics/expansion-location-analyzer.py || echo "⚠️  Skipped"
echo ""

echo "4️⃣  Weekly Insights Generator (for TI Especialistas)"
python3 analytics/weekly-insights-generator.py || echo "⚠️  Skipped"
echo ""

echo "5️⃣  Dying Sectors Detector (avoid waste)"
python3 analytics/dying-sectors-detector.py || echo "⚠️  Skipped"
echo ""

echo "6️⃣  Dark Horses Intelligence (hidden opportunities)"
python3 analytics/dark-horses-intelligence.py || echo "⚠️  Skipped"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ INTELLIGENCE ANALYTICS COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Reports Generated:"
echo ""
echo "   Predictive Intelligence:"
echo "   • analytics/career-trends-latest.txt"
echo "   • analytics/capital-flow-latest.txt"
echo "   • analytics/expansion-locations-latest.txt"
echo "   • analytics/weekly-insights-latest.txt"
echo "   • analytics/dying-sectors-latest.txt"
echo "   • analytics/dark-horses-intelligence-latest.txt"
echo ""
echo "🎯 These reports predict BEFORE the market moves"
echo ""
echo "════════════════════════════════════════════════════════════════"
