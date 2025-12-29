#!/bin/bash

# ============================================================================
# WOMEN'S DATA COLLECTION - ALL SOURCES
# ============================================================================
#
# Collects comprehensive women's data from official sources worldwide:
# - World Bank Gender Portal (60+ countries, 55+ indicators)
# - Eurostat Gender Data (EU countries)
# - FRED US Women's Labor Data
# - ILO Women's Labor Statistics (global)
# - Brazil Women's Data (IBGE, IPEA)
#
# Usage: bash collect-women-data.sh
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "COMPREHENSIVE WOMEN'S DATA COLLECTION"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Started: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
    echo "Virtual environment activated"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
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
    echo "$name"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    TOTAL_COLLECTORS=$((TOTAL_COLLECTORS + 1))

    if [ -f "scripts/$script" ]; then
        if python3 "scripts/$script"; then
            SUCCESSFUL=$((SUCCESSFUL + 1))
            echo ""
            echo "$name completed"
        else
            FAILED=$((FAILED + 1))
            echo ""
            echo "$name failed"
        fi
    else
        echo "Script not found: scripts/$script"
        FAILED=$((FAILED + 1))
    fi

    echo ""
    echo "Waiting 3s before next collector..."
    sleep 3
    echo ""
}

# Run all women's data collectors

echo "Collectors to run:"
echo "   1. World Bank Gender Data (comprehensive)"
echo "   2. Eurostat Gender Data (EU)"
echo "   3. FRED US Women's Labor Data"
echo "   4. ILO Women's Labor Statistics"
echo "   5. Brazil Women's Data (IBGE, IPEA)"
echo ""

# 1. World Bank Gender (comprehensive)
run_collector "World Bank Gender Data (60+ countries)" "collect-women-world-bank.py"

# 2. Eurostat Gender
run_collector "Eurostat Gender Data (EU countries)" "collect-women-eurostat.py"

# 3. FRED US Women
run_collector "FRED US Women's Labor Data" "collect-women-fred.py"

# 4. ILO Global Women's Labor
run_collector "ILO Women's Labor Statistics" "collect-women-ilostat.py"

# 5. Brazil Women's Data
run_collector "Brazil Women's Data (IBGE, IPEA)" "collect-women-brazil.py"

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "WOMEN'S DATA COLLECTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Completed: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""
echo "Summary:"
echo "   Total collectors: $TOTAL_COLLECTORS"
echo "   Successful: $SUCCESSFUL"
echo "   Failed: $FAILED"
echo ""
echo "Data collected:"
echo "   World Bank - 55+ gender indicators, 60+ countries"
echo "   Eurostat - EU gender equality data"
echo "   FRED - US women's employment/earnings"
echo "   ILO - Global women's labor statistics"
echo "   Brazil - IBGE/IPEA women's data"
echo ""
echo "Tables created in sofia schema:"
echo "   - women_world_bank_data"
echo "   - women_eurostat_data"
echo "   - women_fred_data"
echo "   - women_ilo_data"
echo "   - women_brazil_data"
echo ""
echo "Categories covered:"
echo "   - Labor Force Participation"
echo "   - Employment by Sector"
echo "   - Unemployment"
echo "   - Earnings & Gender Pay Gap"
echo "   - Education"
echo "   - Political Participation"
echo "   - Health & Reproductive"
echo "   - Violence Against Women"
echo "   - Legal Rights"
echo ""
