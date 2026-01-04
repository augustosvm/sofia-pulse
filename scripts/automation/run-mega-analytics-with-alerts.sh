#!/bin/bash

################################################################################
# Sofia Pulse - MEGA Analytics WITH WHATSAPP ALERTS
################################################################################

set -e

# Change to project root directory (two levels up from scripts/automation/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Load .env
set -a
source .env 2>/dev/null || true
set +a

# Track failures
FAILED_ANALYTICS=()
TOTAL_ANALYTICS=0
SUCCESS_ANALYTICS=0

# Function to run analytics with tracking
run_analytics() {
    local name="$1"
    local cmd="$2"

    TOTAL_ANALYTICS=$((TOTAL_ANALYTICS + 1))
    echo ""
    echo "▶️  $name..."

    if eval "$cmd" 2>&1; then
        echo "✅ $name - Success"
        SUCCESS_ANALYTICS=$((SUCCESS_ANALYTICS + 1))
    else
        echo "❌ $name - Failed"
        FAILED_ANALYTICS+=("$name")
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo "📊 SOFIA PULSE - MEGA ANALYTICS WITH ALERTS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Start: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Activate venv
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
fi

################################################################################
# CORE ANALYTICS
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "📊 CORE ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Tech Trend Score" "python3 analytics/tech-trend-score-simple.py"
run_analytics "Top 10 Trends" "python3 analytics/top10-tech-trends.py"
run_analytics "Correlations" "python3 analytics/correlation-papers-funding.py"
run_analytics "Dark Horses" "python3 analytics/dark-horses-report.py"
run_analytics "Entity Resolution" "python3 analytics/entity-resolution.py"

################################################################################
# ADVANCED ANALYTICS
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🎯 ADVANCED ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Special Sectors" "python3 analytics/special_sectors_analysis.py"
run_analytics "Early Stage" "python3 analytics/early-stage-deep-dive.py"
run_analytics "Energy Map" "python3 analytics/energy-global-map.py"

################################################################################
# ML ANALYTICS
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🤖 ML ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Causal Insights ML" "bash analytics/run-causal-insights.sh"

################################################################################
# ADVANCED ML ANALYTICS (NEW!)
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🧠 ADVANCED ML ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Jobs Intelligence (NLP)" "python3 analytics/jobs-intelligence.py"
run_analytics "Sentiment Analysis" "python3 analytics/sentiment-analysis.py"
run_analytics "Anomaly Detection" "python3 analytics/anomaly-detection.py"
run_analytics "Time Series Advanced (ARIMA)" "python3 analytics/time-series-advanced.py"
run_analytics "Startup Pattern Matching" "python3 analytics/startup-pattern-matching.py"

################################################################################
# AI-POWERED
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔮 AI-POWERED ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "NLG Playbooks" "python3 analytics/nlg-playbooks-gemini.py"

################################################################################
# INTELLIGENCE ANALYTICS (PREDICTIVE)
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🧠 INTELLIGENCE ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Career Trends" "python3 analytics/career-trends-predictor.py"
run_analytics "Capital Flow" "python3 analytics/capital-flow-predictor.py"
run_analytics "Expansion Locations" "python3 analytics/expansion-location-analyzer.py"
run_analytics "Weekly Insights" "python3 analytics/weekly-insights-generator.py"
run_analytics "Dying Sectors" "python3 analytics/dying-sectors-detector.py"
run_analytics "Dark Horses Intelligence" "python3 analytics/dark-horses-intelligence.py"

################################################################################
# SOCIOECONOMIC INTELLIGENCE
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌍 SOCIOECONOMIC INTELLIGENCE"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Best Cities Tech Talent" "python3 analytics/best-cities-tech-talent.py"
run_analytics "Remote Work Quality" "python3 analytics/remote-work-quality-index.py"
run_analytics "Innovation Hubs" "python3 analytics/intelligence-reports-suite.py"

################################################################################
# NEW DATA ANALYTICS (Women, Security, Social)
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🚺 WOMEN & GENDER ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Women Global Analysis" "python3 analytics/women-global-analysis.py"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔒 SECURITY INTELLIGENCE"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Security Intelligence" "python3 analytics/security-intelligence-report.py"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌐 SOCIAL INTELLIGENCE"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Social Intelligence" "python3 analytics/social-intelligence-report.py"

################################################################################
# BRAZIL SPECIFIC INTELLIGENCE
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🇧🇷 BRAZIL INTELLIGENCE"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Brazil Economy" "python3 analytics/brazil-economy-intelligence.py"

################################################################################
# GLOBAL SPECIALIZED ANALYTICS
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌍 GLOBAL SPECIALIZED ANALYTICS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Global Health" "python3 analytics/global-health-humanitarian.py"
run_analytics "Trade & Agriculture" "python3 analytics/trade-agriculture-intelligence.py"
run_analytics "Tourism" "python3 analytics/tourism-intelligence.py"
run_analytics "LATAM" "python3 analytics/latam-intelligence.py"
run_analytics "Olympics & Sports" "python3 analytics/olympics-sports-intelligence.py"
run_analytics "Base dos Dados" "python3 analytics/basedosdados-intelligence.py"

################################################################################
# CROSS-DATA CORRELATIONS
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔗 CROSS-DATA CORRELATIONS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "Cross-Data Correlations" "python3 analytics/cross-data-correlations.py"

################################################################################
# MEGA ANALYSIS (LAST - combines all)
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌟 MEGA ANALYSIS"
echo "════════════════════════════════════════════════════════════════"

run_analytics "MEGA Analysis" "python3 analytics/mega-analysis.py"

################################################################################
# SUMMARY & WHATSAPP ALERT
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ANALYTICS COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Total analytics: $TOTAL_ANALYTICS"
echo "✅ Success: $SUCCESS_ANALYTICS"
echo "❌ Failed: ${#FAILED_ANALYTICS[@]}"
echo ""

if [ ${#FAILED_ANALYTICS[@]} -gt 0 ]; then
    echo "Failed analytics:"
    for analytics in "${FAILED_ANALYTICS[@]}"; do
        echo "  • $analytics"
    done
    echo ""
fi

# Send WhatsApp summary
if command -v python3 &> /dev/null; then
    python3 -c "
import sys
import os
sys.path.insert(0, 'scripts/utils')

try:
    from whatsapp_notifier import WhatsAppNotifier
    whatsapp = WhatsAppNotifier()

    failed = [$(printf "'%s'," "${FAILED_ANALYTICS[@]}" | sed 's/,$//')]
    total = $TOTAL_ANALYTICS
    success = $SUCCESS_ANALYTICS

    status = '✅' if not failed else '⚠️'
    failures = '\\n'.join([f'• {c}' for c in failed]) if failed else 'None'

    message = f'''{status} Analytics Complete

📊 Total: {total}
✅ Success: {success}
❌ Failed: {len(failed)}

{failures}

📧 Email report will be sent next'''

    whatsapp.send(message)
    print('📱 WhatsApp summary sent')
except Exception as e:
    print(f'⚠️  WhatsApp notification failed: {e}')
"
fi

echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "🎯 Next: bash send-email-mega.sh"
echo ""
