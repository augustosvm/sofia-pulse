#!/bin/bash
################################################################################
# Sofia Pulse - COMPLETE Collection (ALL 55 Collectors)
################################################################################
#
# Runs ALL collectors with:
# - Structured error logging
# - Detailed error messages
# - WhatsApp alerts with error details
# - SQL/API key error detection
#
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env
set -a
source .env 2>/dev/null || true
set +a

# Create log directory
LOG_DIR="/var/log/sofia/collectors"
mkdir -p "$LOG_DIR" 2>/dev/null || LOG_DIR="./logs/collectors"
mkdir -p "$LOG_DIR"

# Date for log files
LOG_DATE=$(date '+%Y-%m-%d')

# Track results
TOTAL_COLLECTORS=0
FAILED_COLLECTORS=()
ERROR_DETAILS=()

################################################################################
# ENHANCED RUN FUNCTION WITH ERROR LOGGING
################################################################################

run_collector() {
    local name="$1"
    local cmd="$2"
    local log_file="$LOG_DIR/${name// /-}-${LOG_DATE}.log"

    TOTAL_COLLECTORS=$((TOTAL_COLLECTORS + 1))
    echo ""
    echo "▶️  [$TOTAL_COLLECTORS/55] $name..."

    # Run collector and capture output + errors
    if output=$($cmd 2>&1 | tee -a "$log_file"); then
        echo "✅ $name - Success"
    else
        exit_code=$?
        echo "❌ $name - Failed (exit code: $exit_code)"

        # Capture last 10 lines of error
        error_snippet=$(tail -10 "$log_file" | head -5)

        # Detect error type
        error_type="Unknown"
        if echo "$error_snippet" | grep -iq "duplicate key\|unique constraint\|foreign key"; then
            error_type="SQL: Duplicate Key"
        elif echo "$error_snippet" | grep -iq "column.*does not exist\|relation.*does not exist"; then
            error_type="SQL: Missing Table/Column"
        elif echo "$error_snippet" | grep -iq "value too long\|varchar"; then
            error_type="SQL: Value Too Long"
        elif echo "$error_snippet" | grep -iq "401\|unauthorized\|api key\|subscription key"; then
            error_type="API: Missing/Invalid Key"
        elif echo "$error_snippet" | grep -iq "403\|forbidden"; then
            error_type="API: Forbidden/Blocked"
        elif echo "$error_snippet" | grep -iq "429\|rate limit"; then
            error_type="API: Rate Limit"
        elif echo "$error_snippet" | grep -iq "timeout\|timed out"; then
            error_type="Network: Timeout"
        elif echo "$error_snippet" | grep -iq "connection refused\|network"; then
            error_type="Network: Connection Failed"
        fi

        # Store failure details
        FAILED_COLLECTORS+=("$name")
        ERROR_DETAILS+=("$name|$error_type|$(echo "$error_snippet" | head -2 | tr '\n' ' ')")
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - COMPLETE COLLECTION (ALL 55 COLLECTORS)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "📁 Log Directory: $LOG_DIR"
echo ""

# Activate Python venv if exists
if [ -d "venv-analytics" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv-analytics/bin/activate
    echo ""
fi

################################################################################
# GROUP 1: FAST APIs (No Rate Limit) - 12 collectors
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "📡 GROUP 1: FAST APIs (No Rate Limit) - 12 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "Electricity Consumption" "python3 scripts/collect-electricity-consumption.py"
run_collector "Port Traffic" "python3 scripts/collect-port-traffic.py"
run_collector "Commodity Prices" "python3 scripts/collect-commodity-prices.py"
run_collector "Semiconductor Sales" "python3 scripts/collect-semiconductor-sales.py"
run_collector "Socioeconomic Indicators" "python3 scripts/collect-socioeconomic-indicators.py"
run_collector "Global Energy Data" "python3 scripts/collect-energy-global.py"
run_collector "HackerNews" "npx tsx scripts/collect-hackernews.ts"
run_collector "NPM Stats" "npx tsx scripts/collect-npm-stats.ts"
run_collector "PyPI Stats" "npx tsx scripts/collect-pypi-stats.ts"
run_collector "ArXiv AI Papers" "npx tsx scripts/collect-arxiv-ai.ts"
run_collector "Space Industry" "npx tsx scripts/collect-space-industry.ts"
run_collector "Cybersecurity CVEs" "npx tsx scripts/collect-cybersecurity.ts"

################################################################################
# GROUP 2: GITHUB (Rate Limited) - 2 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🐙 GROUP 2: GITHUB (Rate Limited) - 2 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "GitHub Trending" "npx tsx scripts/collect-github-trending.ts"
sleep 60

run_collector "GitHub Niches" "npx tsx scripts/collect-github-niches.ts"
sleep 60

################################################################################
# GROUP 3: RESEARCH APIs (Rate Limited) - 5 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📚 GROUP 3: RESEARCH APIs (Rate Limited) - 5 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "Reddit Tech" "npx tsx scripts/collect-reddit-tech.ts"
sleep 60

run_collector "OpenAlex Papers" "npx tsx scripts/collect-openalex.ts"
sleep 60

run_collector "NIH Grants" "npx tsx scripts/collect-nih-grants.ts"
sleep 60

run_collector "Asia Universities" "npx tsx scripts/collect-asia-universities.ts"
sleep 60

run_collector "GDELT Events" "npx tsx scripts/collect-gdelt.ts"
sleep 60

################################################################################
# GROUP 4: PATENTS & IP (Rate Limited) - 4 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📜 GROUP 4: PATENTS & IP (Rate Limited) - 4 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "AI Regulation" "npx tsx scripts/collect-ai-regulation.ts"
sleep 60

run_collector "EPO Patents" "npx tsx scripts/collect-epo-patents.ts"
sleep 60

run_collector "WIPO China Patents" "npx tsx scripts/collect-wipo-china-patents.ts"
sleep 60

run_collector "AI Companies" "npx tsx scripts/collect-ai-companies.ts"
sleep 60

################################################################################
# GROUP 5: INTERNATIONAL ORGANIZATIONS - 8 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌍 GROUP 5: INTERNATIONAL ORGANIZATIONS - 8 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "WHO Health Data" "python3 scripts/collect-who-health.py"
run_collector "UNICEF Child Welfare" "python3 scripts/collect-unicef.py"
run_collector "ILO Labor Statistics" "python3 scripts/collect-ilostat.py"
run_collector "UN Sustainable Dev Goals" "python3 scripts/collect-un-sdg.py"
run_collector "HDX Humanitarian Data" "python3 scripts/collect-hdx-humanitarian.py"
run_collector "WTO Trade Data" "python3 scripts/collect-wto-trade.py"
run_collector "FAO Agriculture Data" "python3 scripts/collect-fao-agriculture.py"
run_collector "CEPAL Latin America" "python3 scripts/collect-cepal-latam.py"

################################################################################
# GROUP 6: WOMEN & GENDER DATA - 6 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "♀️  GROUP 6: WOMEN & GENDER DATA - 6 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "Women World Bank" "python3 scripts/collect-women-world-bank.py"
run_collector "Women Eurostat" "python3 scripts/collect-women-eurostat.py"
run_collector "Women FRED USA" "python3 scripts/collect-women-fred.py"
run_collector "Women ILO Labor" "python3 scripts/collect-women-ilostat.py"
run_collector "Women Brazil" "python3 scripts/collect-women-brazil.py"
run_collector "Central Banks Women" "python3 scripts/collect-central-banks-women.py"

################################################################################
# GROUP 7: BRAZIL OFFICIAL DATA - 6 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🇧🇷 GROUP 7: BRAZIL OFFICIAL DATA - 6 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "BACEN Central Bank" "python3 scripts/collect-bacen-sgs.py"
run_collector "IBGE Official Data" "python3 scripts/collect-ibge-api.py"
run_collector "IPEA Economic Data" "python3 scripts/collect-ipea-api.py"
run_collector "MDIC ComexStat Trade" "python3 scripts/collect-mdic-comexstat.py"
run_collector "Brazil Ministries" "python3 scripts/collect-brazil-ministries.py"
run_collector "Brazil Security 27 States" "python3 scripts/collect-brazil-security.py"

################################################################################
# GROUP 8: SOCIAL & DEMOGRAPHICS - 5 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "👥 GROUP 8: SOCIAL & DEMOGRAPHICS - 5 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "World Religion Data" "python3 scripts/collect-religion-data.py"
run_collector "World NGOs Top 200" "python3 scripts/collect-world-ngos.py"
run_collector "Drugs UNODC Data" "python3 scripts/collect-drugs-data.py"
run_collector "World Security Data" "python3 scripts/collect-world-security.py"
run_collector "World Tourism 90+ Countries" "python3 scripts/collect-world-tourism.py"

################################################################################
# GROUP 9: SPORTS & OLYMPICS - 3 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "⚽ GROUP 9: SPORTS & OLYMPICS - 3 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "Sports Federations FIFA/IOC" "python3 scripts/collect-sports-federations.py"
run_collector "Sports Regional 17 Sports" "python3 scripts/collect-sports-regional.py"
run_collector "World Sports Olympics" "python3 scripts/collect-world-sports.py"

################################################################################
# GROUP 10: OTHER SPECIALIZED - 4 collectors
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔧 GROUP 10: OTHER SPECIALIZED - 4 collectors"
echo "════════════════════════════════════════════════════════════════"

run_collector "World Bank Gender Focus" "python3 scripts/collect-world-bank-gender.py"
run_collector "Base dos Dados Brazil" "python3 scripts/collect-basedosdados.py"
run_collector "Hong Kong IPOs" "npx tsx scripts/collect-hkex-ipos.ts"
run_collector "Cardboard Production" "npx tsx scripts/collect-cardboard-production.ts"

################################################################################
# SUMMARY & DETAILED WHATSAPP ALERT
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ COMPLETE COLLECTION FINISHED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Total collectors: $TOTAL_COLLECTORS"
echo "✅ Success: $((TOTAL_COLLECTORS - ${#FAILED_COLLECTORS[@]}))"
echo "❌ Failed: ${#FAILED_COLLECTORS[@]}"
echo ""

if [ ${#FAILED_COLLECTORS[@]} -gt 0 ]; then
    echo "Failed collectors with error details:"
    echo ""

    for detail in "${ERROR_DETAILS[@]}"; do
        IFS='|' read -r name error_type error_msg <<< "$detail"
        echo "  ❌ $name"
        echo "     Error: $error_type"
        echo "     Details: $error_msg"
        echo ""
    done
fi

# Send DETAILED WhatsApp summary
if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, 'scripts/utils')

try:
    from whatsapp_notifier import WhatsAppNotifier
    whatsapp = WhatsAppNotifier()

    # Read error details from environment
    total = int(os.environ.get('TOTAL_COLLECTORS', '0'))
    failed_count = int(os.environ.get('FAILED_COUNT', '0'))
    success = total - failed_count

    # Parse error details
    error_details_str = os.environ.get('ERROR_DETAILS', '')

    status = '✅' if failed_count == 0 else '⚠️'

    message = f'''{status} Complete Collection Report

📊 Total: {total}
✅ Success: {success}
❌ Failed: {failed_count}'''

    if error_details_str:
        message += "\n\n" + "Errors:\n" + error_details_str

    message += f"\n\n📁 Logs: /var/log/sofia/collectors/"

    whatsapp.send(message)
    print('📱 WhatsApp detailed summary sent')
except Exception as e:
    print(f'⚠️  WhatsApp notification failed: {e}')
PYTHON_SCRIPT
fi

echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "📁 Logs saved to: $LOG_DIR"
echo ""
