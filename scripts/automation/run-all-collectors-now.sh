#!/bin/bash

################################################################################
# Sofia Pulse - Run ALL Collectors NOW
# Executa todos os collectors: diários, semanais e mensais
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Create logs directory
mkdir -p logs

echo "════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - RUN ALL COLLECTORS NOW"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏰ Started: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""

TOTAL=0
SUCCESS=0
FAILED=0

run_collector() {
    local name=$1
    local command=$2

    echo "════════════════════════════════════════════════════════════════"
    echo "📊 $name"
    echo "════════════════════════════════════════════════════════════════"

    TOTAL=$((TOTAL + 1))

    if eval "$command" 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        echo "✅ $name completed"
    else
        FAILED=$((FAILED + 1))
        echo "❌ $name failed"
    fi

    echo ""
    sleep 2
}

# ============================================================================
# DAILY COLLECTORS
# ============================================================================

echo "📅 DAILY COLLECTORS"
echo ""

run_collector "Fast APIs Collection" "bash collect-fast-apis.sh"
run_collector "Limited APIs with Alerts" "bash collect-limited-apis-with-alerts.sh"

# ============================================================================
# WEEKLY COLLECTORS
# ============================================================================

echo ""
echo "📆 WEEKLY COLLECTORS"
echo ""

run_collector "Women Data (5 collectors)" "bash collect-women-data.sh"
run_collector "World Security" "python3 scripts/collect-world-security.py"
run_collector "Brazil Security" "python3 scripts/collect-brazil-security.py"
run_collector "World Tourism" "python3 scripts/collect-world-tourism.py"
run_collector "Sports Regional" "python3 scripts/collect-sports-regional.py"
run_collector "Drugs Data" "python3 scripts/collect-drugs-data.py"

# ============================================================================
# MONTHLY COLLECTORS
# ============================================================================

echo ""
echo "📅 MONTHLY COLLECTORS"
echo ""

run_collector "World NGOs" "python3 scripts/collect-world-ngos.py"
run_collector "Religion Data" "python3 scripts/collect-religion-data.py"
run_collector "Sports Federations" "python3 scripts/collect-sports-federations.py"
run_collector "Central Banks Women" "python3 scripts/collect-central-banks-women.py"
run_collector "Brazil Ministries" "python3 scripts/collect-brazil-ministries.py"

# ============================================================================
# INTERNATIONAL ORGANIZATIONS
# ============================================================================

echo ""
echo "🌍 INTERNATIONAL ORGANIZATIONS"
echo ""

run_collector "International Orgs (9 collectors)" "bash collect-international-orgs.sh"

# ============================================================================
# SUMMARY
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL COLLECTORS COMPLETED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏰ Completed: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""
echo "📊 Summary:"
echo "   Total collectors: $TOTAL"
echo "   Successful: $SUCCESS"
echo "   Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL COLLECTORS SUCCEEDED!"
else
    echo "⚠️  Some collectors failed. Check logs for details."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📝 Next steps:"
echo ""
echo "1. Run analytics:"
echo "   bash run-mega-analytics-with-alerts.sh"
echo ""
echo "2. Send email:"
echo "   bash send-email-mega.sh"
echo ""
echo "3. Send WhatsApp reports:"
echo "   python3 send-reports-whatsapp.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"
