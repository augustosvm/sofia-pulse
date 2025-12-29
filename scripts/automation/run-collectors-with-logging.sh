#!/bin/bash
################################################################################
# Sofia Pulse - Run Collectors with Enhanced Error Logging
# Captures all errors and sends immediate WhatsApp alerts for critical failures
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env
set -a
source .env 2>/dev/null || true
set +a

# Create log directories
LOG_DIR="/var/log/sofia"
mkdir -p "$LOG_DIR" 2>/dev/null || LOG_DIR="./logs/sofia"
mkdir -p "$LOG_DIR"

# Date for logs
DATE=$(date '+%Y-%m-%d')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Track results
TOTAL_COLLECTORS=0
FAILED_COLLECTORS=()
SUCCESS_COLLECTORS=()

################################################################################
# ENHANCED RUN FUNCTION WITH IMMEDIATE ERROR ALERTS
################################################################################

run_collector() {
    local name="$1"
    local cmd="$2"
    local frequency="$3"  # hourly, daily, weekly, monthly
    local log_file="$LOG_DIR/${name// /-}-${DATE}.log"

    TOTAL_COLLECTORS=$((TOTAL_COLLECTORS + 1))

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶️  [$TOTAL_COLLECTORS] $name ($frequency)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Log start
    echo "[$TIMESTAMP] Starting $name" >> "$log_file"

    # Run collector and capture output
    if output=$(eval "$cmd" 2>&1 | tee -a "$log_file"); then
        echo "✅ $name - SUCCESS"
        SUCCESS_COLLECTORS+=("$name")
        echo "[$TIMESTAMP] ✅ SUCCESS" >> "$log_file"
    else
        exit_code=$?
        echo "❌ $name - FAILED (exit code: $exit_code)"
        FAILED_COLLECTORS+=("$name")
        echo "[$TIMESTAMP] ❌ FAILED (exit code: $exit_code)" >> "$log_file"

        # Extract and analyze error
        error_snippet=$(tail -20 "$log_file" | grep -i "error\|exception\|failed\|traceback" | tail -5 || echo "Unknown error")

        # Send immediate WhatsApp alert for critical errors
        if echo "$error_snippet" | grep -iq "table.*does not exist\|column.*does not exist\|missing.*key"; then
            python3 << PYTHON_ALERT
import sys
sys.path.insert(0, 'scripts/utils')
try:
    from whatsapp_notifier import WhatsAppNotifier
    from error_analyzer import ErrorAnalyzer

    whatsapp = WhatsAppNotifier()
    analyzer = ErrorAnalyzer()

    error_text = """$error_snippet"""
    category, short_msg, details = analyzer.analyze_error(error_text)

    alert = f"""🚨 ERRO CRÍTICO

Collector: $name
Categoria: {category}
Erro: {short_msg}
{details}

⏰ {TIMESTAMP}

Ação necessária AGORA!"""

    whatsapp.send(alert)
except:
    pass
PYTHON_ALERT
        fi
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - COLLECTORS WITH LOGGING"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Started: $TIMESTAMP"
echo "📁 Logs: $LOG_DIR"
echo ""

# Activate Python venv if exists
if [ -d "venv-analytics" ]; then
    echo "🐍 Activating Python environment..."
    source venv-analytics/bin/activate
fi

################################################################################
# FREQUENCY-BASED COLLECTION
################################################################################

# Determine what to run based on time and day
HOUR=$(date +%H)
DAY=$(date +%u)  # 1-7 (Mon-Sun)
DOM=$(date +%d)  # Day of month

RUN_HOURLY=false
RUN_DAILY=false
RUN_WEEKLY=false
RUN_MONTHLY=false

# Hourly collectors run every 3 hours during business hours
if [ "$HOUR" -eq 8 ] || [ "$HOUR" -eq 11 ] || [ "$HOUR" -eq 14 ] || [ "$HOUR" -eq 17 ] || [ "$HOUR" -eq 20 ]; then
    RUN_HOURLY=true
fi

# Daily collectors run once per day
if [ "$HOUR" -eq 10 ]; then
    RUN_DAILY=true
fi

# Weekly collectors run on Mondays
if [ "$DAY" -eq 1 ] && [ "$HOUR" -eq 13 ]; then
    RUN_WEEKLY=true
fi

# Monthly collectors run on first Monday
if [ "$DAY" -eq 1 ] && [ "$DOM" -le 7 ] && [ "$HOUR" -eq 14 ]; then
    RUN_MONTHLY=true
fi

################################################################################
# HOURLY COLLECTORS (if enabled)
################################################################################

if [ "$RUN_HOURLY" = true ]; then
    echo ""
    echo "🔄 HOURLY COLLECTORS (High Frequency Data)"
    echo "════════════════════════════════════════════════════════════════"

    run_collector "HackerNews" "npx tsx scripts/collect-hackernews.ts" "hourly"
    run_collector "Reddit Tech" "npx tsx scripts/collect-reddit-tech.ts" "hourly"
    run_collector "NPM Stats" "npx tsx scripts/collect-npm-stats.ts" "hourly"
    run_collector "PyPI Stats" "npx tsx scripts/collect-pypi-stats.ts" "hourly"
    run_collector "GitHub Trending" "npx tsx scripts/collect-github-trending.ts" "hourly"
    run_collector "GitHub Niches" "npx tsx scripts/collect-github-niches.ts" "hourly"
    run_collector "GDELT Events" "npx tsx scripts/collect-gdelt.ts" "hourly"
fi

################################################################################
# DAILY COLLECTORS (if enabled)
################################################################################

if [ "$RUN_DAILY" = true ]; then
    echo ""
    echo "📅 DAILY COLLECTORS"
    echo "════════════════════════════════════════════════════════════════"

    # Brazil (6)
    run_collector "BACEN SGS" "python3 scripts/collect-bacen-sgs.py" "daily"
    run_collector "IBGE API" "python3 scripts/collect-ibge-api.py" "daily"
    run_collector "IPEA API" "python3 scripts/collect-ipea-api.py" "daily"
    run_collector "MDIC ComexStat" "python3 scripts/collect-mdic-comexstat.py" "daily"
    run_collector "Brazil Ministries" "python3 scripts/collect-brazil-ministries.py" "daily"
    run_collector "Brazil Security" "python3 scripts/collect-brazil-security.py" "daily"

    # Energy & Commodities (4)
    run_collector "Electricity" "python3 scripts/collect-electricity-consumption.py" "daily"
    run_collector "Energy Global" "python3 scripts/collect-energy-global.py" "daily"
    run_collector "Commodities" "python3 scripts/collect-commodity-prices.py" "daily"
    run_collector "Port Traffic" "python3 scripts/collect-port-traffic.py" "daily"

    # Research (3)
    run_collector "ArXiv AI" "npx tsx scripts/collect-arxiv-ai.ts" "daily"
    run_collector "OpenAlex" "npx tsx scripts/collect-openalex.ts" "daily"
    run_collector "NIH Grants" "npx tsx scripts/collect-nih-grants.ts" "daily"

    # Patents (4)
    run_collector "EPO Patents" "npx tsx scripts/collect-epo-patents.ts" "daily"
    run_collector "WIPO Patents" "npx tsx scripts/collect-wipo-china-patents.ts" "daily"
    run_collector "AI Regulation" "npx tsx scripts/collect-ai-regulation.ts" "daily"
    run_collector "AI Companies" "npx tsx scripts/collect-ai-companies.ts" "daily"

    # Security & Space (2)
    run_collector "Cybersecurity" "npx tsx scripts/collect-cybersecurity.ts" "daily"
    run_collector "Space Industry" "npx tsx scripts/collect-space-industry.ts" "daily"

    # International Orgs (8)
    run_collector "WHO Health" "python3 scripts/collect-who-health.py" "daily"
    run_collector "UNICEF" "python3 scripts/collect-unicef.py" "daily"
    run_collector "ILO Stats" "python3 scripts/collect-ilostat.py" "daily"
    run_collector "UN SDG" "python3 scripts/collect-un-sdg.py" "daily"
    run_collector "HDX Humanitarian" "python3 scripts/collect-hdx-humanitarian.py" "daily"
    run_collector "WTO Trade" "python3 scripts/collect-wto-trade.py" "daily"
    run_collector "FAO Agriculture" "python3 scripts/collect-fao-agriculture.py" "daily"
    run_collector "CEPAL LATAM" "python3 scripts/collect-cepal-latam.py" "daily"

    # Tourism & Trade (2)
    run_collector "World Tourism" "python3 scripts/collect-world-tourism.py" "daily"
    run_collector "World Security" "python3 scripts/collect-world-security.py" "daily"

    # Manufacturing (2)
    run_collector "Semiconductors" "python3 scripts/collect-semiconductor-sales.py" "daily"
    run_collector "Cardboard" "npx tsx scripts/collect-cardboard-production.ts" "daily"

    # IPOs (1)
    run_collector "Hong Kong IPOs" "npx tsx scripts/collect-hkex-ipos.ts" "daily"
fi

################################################################################
# WEEKLY COLLECTORS (if enabled)
################################################################################

if [ "$RUN_WEEKLY" = true ]; then
    echo ""
    echo "📆 WEEKLY COLLECTORS (Mondays)"
    echo "════════════════════════════════════════════════════════════════"

    # Women & Gender (6)
    run_collector "Women World Bank" "python3 scripts/collect-women-world-bank.py" "weekly"
    run_collector "Women Eurostat" "python3 scripts/collect-women-eurostat.py" "weekly"
    run_collector "Women FRED" "python3 scripts/collect-women-fred.py" "weekly"
    run_collector "Women ILO" "python3 scripts/collect-women-ilostat.py" "weekly"
    run_collector "Women Brazil" "python3 scripts/collect-women-brazil.py" "weekly"
    run_collector "Central Banks Women" "python3 scripts/collect-central-banks-women.py" "weekly"

    # Sports (3)
    run_collector "Sports Federations" "python3 scripts/collect-sports-federations.py" "weekly"
    run_collector "Sports Regional" "python3 scripts/collect-sports-regional.py" "weekly"
    run_collector "World Sports" "python3 scripts/collect-world-sports.py" "weekly"

    # Universities (1)
    run_collector "Asia Universities" "npx tsx scripts/collect-asia-universities.ts" "weekly"
fi

################################################################################
# MONTHLY COLLECTORS (if enabled)
################################################################################

if [ "$RUN_MONTHLY" = true ]; then
    echo ""
    echo "📌 MONTHLY COLLECTORS (1st Monday)"
    echo "════════════════════════════════════════════════════════════════"

    run_collector "Socioeconomic Indicators" "python3 scripts/collect-socioeconomic-indicators.py" "monthly"
    run_collector "Religion Data" "python3 scripts/collect-religion-data.py" "monthly"
    run_collector "World NGOs" "python3 scripts/collect-world-ngos.py" "monthly"
    run_collector "Drugs Data" "python3 scripts/collect-drugs-data.py" "monthly"
    run_collector "World Bank Gender" "python3 scripts/collect-world-bank-gender.py" "monthly"
    run_collector "Base dos Dados" "python3 scripts/collect-basedosdados.py" "monthly"
fi

################################################################################
# SUMMARY
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ COLLECTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📊 Total: $TOTAL_COLLECTORS"
echo "✅ Success: ${#SUCCESS_COLLECTORS[@]}"
echo "❌ Failed: ${#FAILED_COLLECTORS[@]}"
echo ""

if [ ${#FAILED_COLLECTORS[@]} -gt 0 ]; then
    echo "Failed collectors:"
    for collector in "${FAILED_COLLECTORS[@]}"; do
        echo "  • $collector"
    done
    echo ""
fi

echo "📁 Logs saved to: $LOG_DIR"
echo ""
