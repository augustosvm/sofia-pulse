#!/bin/bash

################################################################################
# SOFIA PULSE - SOCIOECONOMIC INTELLIGENCE REPORTS
# Runs 6 reports based on World Bank socioeconomic indicators
# Uses established methodologies (HDI, GII, Numbeo, INSEAD, etc.)
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
echo "🌍 SOFIA PULSE - SOCIOECONOMIC INTELLIGENCE REPORTS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Tempo estimado: 2-4 minutos"
echo "📈 Gerará 6 relatórios baseados em metodologias consagradas"
echo "📊 Fonte: World Bank Socioeconomic Indicators (92k+ records)"
echo ""

# Activate virtual environment
source venv-analytics/bin/activate

echo "════════════════════════════════════════════════════════════════"
echo "🎯 SOCIOECONOMIC INTELLIGENCE"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Best Cities for Tech Talent"
echo "   Methodology: INSEAD Global Talent Competitiveness Index"
python3 analytics/best-cities-tech-talent.py || echo "⚠️  Skipped"
echo ""

echo "2️⃣  Remote Work Quality Index"
echo "   Methodology: Nomad List Index + Numbeo QoL"
python3 analytics/remote-work-quality-index.py || echo "⚠️  Skipped"
echo ""

echo "3️⃣  Intelligence Reports Suite (4 reports)"
echo "   Generates:"
echo "   • Innovation Hubs Ranking (WIPO GII)"
echo "   • Best Countries for Startup Founders (World Bank Ease of Doing Business)"
echo "   • Digital Nomad Index (Nomad List)"
echo "   • STEM Education Leaders (OECD PISA inspired)"
python3 analytics/intelligence-reports-suite.py || echo "⚠️  Skipped"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ SOCIOECONOMIC INTELLIGENCE COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Reports Generated:"
echo ""
echo "   Global Rankings (6 total):"
echo "   • analytics/best-cities-tech-talent-latest.txt"
echo "   • analytics/remote-work-quality-latest.txt"
echo "   • analytics/innovation-hubs-latest.txt"
echo "   • analytics/startup-founders-latest.txt"
echo "   • analytics/digital-nomad-latest.txt"
echo "   • analytics/stem-education-latest.txt"
echo ""
echo "📚 Methodologies documented in: analytics/METHODOLOGIES.md"
echo ""
echo "🎯 All reports use established methodologies from:"
echo "   • UNDP (Human Development Index)"
echo "   • WIPO/Cornell (Global Innovation Index)"
echo "   • Numbeo/Mercer (Quality of Life)"
echo "   • World Bank (Ease of Doing Business)"
echo "   • Nomad List (Digital Nomad Index)"
echo "   • INSEAD (Global Talent Index)"
echo "   • OECD (PISA Education Assessment)"
echo ""
echo "════════════════════════════════════════════════════════════════"
