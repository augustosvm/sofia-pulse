#!/bin/bash

# ============================================================================
# INTERNATIONAL ORGANIZATIONS DATA COLLECTION
# ============================================================================
#
# Collects data from major international organizations:
# - World Bank (Gender, Development)
# - UN SDG (Sustainable Development Goals)
# - WTO (World Trade Organization)
# - ILO (International Labour Organization)
# - UNICEF (Children's data)
# - WHO (World Health Organization)
# - FAO (Food and Agriculture)
# - HDX (Humanitarian Data Exchange)
# - CEPAL/ECLAC (Latin America)
#
# Usage: bash collect-international-orgs.sh
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "🌍 INTERNATIONAL ORGANIZATIONS DATA COLLECTION"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Started: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
    echo "✅ Virtual environment activated"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

echo ""

# Track results
TOTAL_COLLECTORS=0
SUCCESSFUL=0
FAILED=0

# Function to run collector
run_collector() {
    local name=$1
    local script=$2

    echo "════════════════════════════════════════════════════════════════"
    echo "📊 $name"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    TOTAL_COLLECTORS=$((TOTAL_COLLECTORS + 1))

    if [ -f "scripts/$script" ]; then
        if python3 "scripts/$script"; then
            SUCCESSFUL=$((SUCCESSFUL + 1))
            echo ""
            echo "✅ $name completed"
        else
            FAILED=$((FAILED + 1))
            echo ""
            echo "❌ $name failed"
        fi
    else
        echo "⚠️  Script not found: scripts/$script"
        FAILED=$((FAILED + 1))
    fi

    echo ""
    echo "⏳ Waiting 5s before next collector..."
    sleep 5
    echo ""
}

# Run all collectors

echo "📋 Collectors to run:"
echo "   1. World Bank Gender Data"
echo "   2. UN SDG Indicators"
echo "   3. WTO Trade Data"
echo "   4. ILO Labor Statistics"
echo "   5. UNICEF Children Data"
echo "   6. WHO Health Data"
echo "   7. FAO Agriculture Data"
echo "   8. HDX Humanitarian Data"
echo "   9. CEPAL/ECLAC Latin America"
echo ""

# 1. World Bank Gender
run_collector "World Bank Gender Data" "collect-world-bank-gender.py"

# 2. UN SDG
run_collector "UN SDG Indicators" "collect-un-sdg.py"

# 3. WTO Trade
run_collector "WTO Trade Data" "collect-wto-trade.py"

# 4. ILO Labor
run_collector "ILO Labor Statistics" "collect-ilostat.py"

# 5. UNICEF
run_collector "UNICEF Children Data" "collect-unicef.py"

# 6. WHO Health
run_collector "WHO Health Data" "collect-who-health.py"

# 7. FAO Agriculture
run_collector "FAO Agriculture Data" "collect-fao-agriculture.py"

# 8. HDX Humanitarian
run_collector "HDX Humanitarian Data" "collect-hdx-humanitarian.py"

# 9. CEPAL Latin America
run_collector "CEPAL/ECLAC Latin America" "collect-cepal-latam.py"

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "✅ INTERNATIONAL ORGANIZATIONS COLLECTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Completed: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""
echo "📊 Summary:"
echo "   Total collectors: $TOTAL_COLLECTORS"
echo "   Successful: $SUCCESSFUL"
echo "   Failed: $FAILED"
echo ""
echo "📦 Data collected from:"
echo "   🏦 World Bank - Gender indicators"
echo "   🎯 UN SDG - Development goals"
echo "   🚢 WTO - International trade"
echo "   👷 ILO - Labor statistics"
echo "   👶 UNICEF - Children's welfare"
echo "   🏥 WHO - Global health"
echo "   🌾 FAO - Agriculture"
echo "   🆘 HDX - Humanitarian data"
echo "   🌎 CEPAL - Latin America"
echo ""
echo "💡 Tables created in sofia schema:"
echo "   • gender_indicators"
echo "   • sdg_indicators"
echo "   • wto_trade_data"
echo "   • ilo_labor_data"
echo "   • unicef_children_data"
echo "   • who_health_data"
echo "   • fao_agriculture_data"
echo "   • hdx_humanitarian_data"
echo "   • cepal_latam_data"
echo "   • cepal_femicide"
echo ""
