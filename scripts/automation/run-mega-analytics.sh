#!/bin/bash
# ============================================================================
# SOFIA PULSE - MEGA ANALYTICS
# ============================================================================
# Executa TODAS as análises disponíveis
# Tempo estimado: 5-8 minutos
# ============================================================================

set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "============================================================================"
echo "📊 SOFIA PULSE - MEGA ANALYTICS"
echo "============================================================================"
echo ""
echo "⏱️  Tempo estimado: 8-12 minutos"
echo "📈 Gerará 17 relatórios completos (11 core + 6 intelligence)"
echo ""

# Activate virtual environment
source venv-analytics/bin/activate

# Create analytics directory if it doesn't exist
mkdir -p analytics

# ============================================================================
# CORE ANALYTICS
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "📊 CORE ANALYTICS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Top 10 Tech Trends"
python3 analytics/top10-tech-trends.py || echo "⚠️  Skipped"
echo ""

echo "2️⃣  Tech Trend Scoring (Complete)"
python3 analytics/tech-trend-score-simple.py || echo "⚠️  Skipped"
echo ""

echo "3️⃣  Correlations: Papers ↔ Funding"
python3 analytics/correlation-papers-funding.py || echo "⚠️  Skipped"
echo ""

echo "4️⃣  Dark Horses Report"
python3 analytics/dark-horses-report.py || echo "⚠️  Skipped"
echo ""

echo "5️⃣  Entity Resolution (Fuzzy Matching)"
python3 analytics/entity-resolution.py || echo "⚠️  Skipped"
echo ""

# ============================================================================
# ADVANCED ANALYTICS
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "🎯 ADVANCED ANALYTICS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "6️⃣  Special Sectors Analysis"
python3 analytics/special_sectors_analysis.py || echo "⚠️  Skipped"
echo ""

echo "7️⃣  Early-Stage Deep Dive"
python3 analytics/early-stage-deep-dive.py || echo "⚠️  Skipped"
echo ""

echo "8️⃣  Global Energy Map"
python3 analytics/energy-global-map.py || echo "⚠️  Skipped"
echo ""

echo "9️⃣  Causal Insights ML (Sklearn + Clustering + NLP + Time Series)"
bash run-causal-insights.sh || echo "⚠️  Skipped"
echo ""

# ============================================================================
# AI-POWERED ANALYTICS
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "🤖 AI-POWERED ANALYTICS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "🔟 NLG Playbooks (Gemini AI)"
if [ -n "$GEMINI_API_KEY" ] && [ "$GEMINI_API_KEY" != "your-gemini-api-key-here" ]; then
    python3 analytics/nlg-playbooks-gemini.py || echo "⚠️  Skipped"
else
    echo "⚠️  GEMINI_API_KEY not configured - Skipping"
fi
echo ""

# ============================================================================
# MEGA ANALYSIS (NEW!)
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "🌍 MEGA ANALYSIS (ALL DATA SOURCES)"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣1️⃣  MEGA Analysis (Comprehensive Cross-Database)"
python3 analytics/mega-analysis.py || echo "⚠️  Skipped"
echo ""

# ============================================================================
# INTELLIGENCE ANALYTICS (PREDICTIVE)
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "🧠 INTELLIGENCE ANALYTICS (PREDICTIVE)"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Running predictive intelligence analyses..."
echo ""
bash run-intelligence-analytics.sh || echo "⚠️  Intelligence Analytics skipped"
echo ""

# ============================================================================
# SOCIOECONOMIC INTELLIGENCE (NEW!)
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "🌍 SOCIOECONOMIC INTELLIGENCE (GLOBAL RANKINGS)"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Running socioeconomic intelligence reports (established methodologies)..."
echo ""
bash run-socioeconomic-reports.sh || echo "⚠️  Socioeconomic Reports skipped"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ ANALYTICS COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Reports Generated:"
echo ""
echo "   Core Analytics:"
echo "   • analytics/top10-latest.txt"
echo "   • analytics/sofia-report.txt"
echo "   • analytics/correlation-latest.txt"
echo "   • analytics/dark-horses-latest.txt"
echo "   • analytics/entity-resolution-latest.txt"
echo ""
echo "   Advanced Analytics:"
echo "   • analytics/special-sectors-latest.txt"
echo "   • analytics/early-stage-latest.txt"
echo "   • analytics/energy-global-latest.txt"
echo "   • analytics/causal-insights-latest.txt (ML + Clustering + NLP + Forecast)"
echo ""
echo "   AI-Powered:"
echo "   • analytics/playbook-latest.txt (if Gemini configured)"
echo ""
echo "   🌍 MEGA Analysis:"
echo "   • analytics/mega-analysis-latest.txt"
echo ""
echo "   🧠 Intelligence Analytics (PREDICTIVE):"
echo "   • analytics/career-trends-latest.txt"
echo "   • analytics/capital-flow-latest.txt"
echo "   • analytics/expansion-locations-latest.txt"
echo "   • analytics/weekly-insights-latest.txt"
echo "   • analytics/dying-sectors-latest.txt"
echo "   • analytics/dark-horses-intelligence-latest.txt"
echo ""
echo "   🌍 Socioeconomic Intelligence (GLOBAL RANKINGS):"
echo "   • analytics/best-cities-tech-talent-latest.txt"
echo "   • analytics/remote-work-quality-latest.txt"
echo "   • analytics/innovation-hubs-latest.txt"
echo "   • analytics/startup-founders-latest.txt"
echo "   • analytics/digital-nomad-latest.txt"
echo "   • analytics/stem-education-latest.txt"
echo ""
echo "🎯 Total: 23 reports (11 core + 6 predictive + 6 socioeconomic)"
echo "🎯 Next Step: Send all reports by email with send-email-mega.sh"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
