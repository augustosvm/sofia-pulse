#!/bin/bash
################################################################################
# SOFIA PULSE - MEGA ANALYTICS RUNNER WITH ALERTS
# Runs all 31 analytics and sends WhatsApp alerts
################################################################################

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtualenv
source venv-analytics/bin/activate

ANALYTICS_DIR="analytics"
SUCCESS=0
FAILED=0
FAILED_LIST=()

echo "════════════════════════════════════════════════════════════════"
echo "🧠 RUNNING ALL ANALYTICS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Function to run analytics
run_analytics() {
    local name="$1"
    local script="$2"

    echo "📊 Running: $name..."

    if python3 "$ANALYTICS_DIR/$script" > /dev/null 2>&1; then
        echo "   ✅ $name - Success"
        ((SUCCESS++))
    else
        echo "   ❌ $name - Failed"
        ((FAILED++))
        FAILED_LIST+=("$name")
    fi
}

# Core Analytics
run_analytics "Tech Trend Score" "tech-trend-score-simple.py"
run_analytics "Top 10 Tech Trends" "top10-tech-trends.py"
run_analytics "Correlations Papers-Funding" "correlation-papers-funding.py"
run_analytics "Dark Horses Report" "dark-horses-report.py"
run_analytics "Entity Resolution" "entity-resolution.py"

# Advanced Analytics
run_analytics "Special Sectors" "special_sectors_analysis.py"
run_analytics "Early Stage Deep Dive" "early-stage-deep-dive.py"
run_analytics "Energy Global Map" "energy-global-map.py"

# ML Analytics
run_analytics "Causal Insights ML" "causal-insights-ml.py"
run_analytics "Anomaly Detection" "anomaly-detection.py"
run_analytics "Time Series Advanced" "time-series-advanced.py"
run_analytics "Startup Pattern Matching" "startup-pattern-matching.py"
run_analytics "Jobs Intelligence" "jobs-intelligence.py"
run_analytics "Sentiment Analysis" "sentiment-analysis.py"

# AI-Powered
run_analytics "NLG Playbooks" "nlg-playbooks-gemini.py"

# MEGA Analysis
run_analytics "MEGA Analysis" "mega-analysis.py"

# Predictive Intelligence
run_analytics "Career Trends" "career-trends-predictor.py"
run_analytics "Capital Flow" "capital-flow-predictor.py"
run_analytics "Expansion Locations" "expansion-location-analyzer.py"
run_analytics "Weekly Insights" "weekly-insights-generator.py"
run_analytics "Dying Sectors" "dying-sectors-detector.py"
run_analytics "Dark Horses Intelligence" "dark-horses-intelligence.py"

# Socioeconomic Intelligence
run_analytics "Best Cities Tech Talent" "best-cities-tech-talent.py"
run_analytics "Remote Work Quality" "remote-work-quality-index.py"
run_analytics "Innovation Hubs" "intelligence-reports-suite.py"

# Additional Intelligence
run_analytics "Women Global Analysis" "women-global-analysis.py"
run_analytics "Security Intelligence" "security-intelligence-report.py"
run_analytics "Social Intelligence" "social-intelligence-report.py"
run_analytics "Brazil Economy" "brazil-economy-intelligence.py"
run_analytics "Global Health" "global-health-humanitarian.py"
run_analytics "Trade & Agriculture" "trade-agriculture-intelligence.py"
run_analytics "Tourism" "tourism-intelligence.py"
run_analytics "LATAM" "latam-intelligence.py"
run_analytics "Olympics & Sports" "olympics-sports-intelligence.py"
run_analytics "Base dos Dados" "basedosdados-intelligence.py"
run_analytics "Cross-Data Correlations" "cross-data-correlations.py"

# Catho Intelligence
run_analytics "Catho Jobs Intelligence" "catho-jobs-intelligence.py"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ANALYTICS COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Total analytics: $((SUCCESS + FAILED))"
echo "✅ Success: $SUCCESS"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "Failed analytics:"
    for item in "${FAILED_LIST[@]}"; do
        echo "  • $item"
    done
    echo ""
fi

# Send WhatsApp summary
if command -v python3 &> /dev/null; then
    python3 scripts/utils/whatsapp_notifier.py "📊 Analytics Complete: $SUCCESS success, $FAILED failed" 2>/dev/null || true
fi

echo "⏱️  Completed: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""
echo "🎯 Next: python3 send-email-mega.py"
