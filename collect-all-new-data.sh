#!/bin/bash

# ============================================================================
# COLLECT ALL NEW DATA SOURCES
# ============================================================================
#
# Executa todos os coletores novos:
# - Mulheres (5 coletores)
# - Seguranca (2 coletores)
# - Esportes (3 coletores)
# - Turismo, Ministerios, Drogas, Religiao, ONGs, Bancos Centrais
#
# Usage: bash collect-all-new-data.sh
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "COLLECTING ALL NEW DATA SOURCES"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Started: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""

cd "$(dirname "$0")"

# Activate venv if exists
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

TOTAL=0
SUCCESS=0
FAILED=0

run() {
    local name=$1
    local script=$2
    echo "════════════════════════════════════════════════════════════════"
    echo "$name"
    echo "════════════════════════════════════════════════════════════════"
    TOTAL=$((TOTAL + 1))
    if python3 "scripts/$script" 2>&1; then
        SUCCESS=$((SUCCESS + 1))
        echo "Completed"
    else
        FAILED=$((FAILED + 1))
        echo "FAILED"
    fi
    echo ""
    sleep 2
}

echo "=== WOMEN'S DATA (5 collectors) ==="
run "Women - World Bank (55+ indicators)" "collect-women-world-bank.py"
run "Women - Eurostat (EU)" "collect-women-eurostat.py"
run "Women - FRED (USA)" "collect-women-fred.py"
run "Women - ILO (Global, Asia focus)" "collect-women-ilostat.py"
run "Women - Brazil (IBGE/IPEA)" "collect-women-brazil.py"

echo "=== SECURITY DATA (2 collectors) ==="
run "Security - Brazil (states + cities)" "collect-brazil-security.py"
run "Security - World (Americas, Europe, Asia)" "collect-world-security.py"

echo "=== SPORTS DATA (3 collectors) ==="
run "Sports - Physical Activity (WHO)" "collect-world-sports.py"
run "Sports - Federations (FIFA, IOC, etc)" "collect-sports-federations.py"
run "Sports - Regional (17 sports)" "collect-sports-regional.py"

echo "=== OTHER DATA (6 collectors) ==="
run "Tourism - World (90+ countries)" "collect-world-tourism.py"
run "Brazil Ministries (12 ministries)" "collect-brazil-ministries.py"
run "Drugs - World (UNODC, state level)" "collect-drugs-data.py"
run "Religion - World (40+ countries)" "collect-religion-data.py"
run "NGOs - Top 200 World" "collect-world-ngos.py"
run "Central Banks Women Data" "collect-central-banks-women.py"

echo "════════════════════════════════════════════════════════════════"
echo "ALL NEW DATA COLLECTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Completed: $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
echo ""
echo "Summary:"
echo "   Total collectors: $TOTAL"
echo "   Successful: $SUCCESS"
echo "   Failed: $FAILED"
echo ""
echo "Tables created in sofia schema:"
echo "   - women_world_bank_data"
echo "   - women_eurostat_data"
echo "   - women_fred_data"
echo "   - women_ilo_data"
echo "   - women_brazil_data"
echo "   - brazil_security_data"
echo "   - brazil_security_cities"
echo "   - world_security_data"
echo "   - world_sports_data"
echo "   - sports_federations"
echo "   - sports_rankings"
echo "   - olympics_medals"
echo "   - sports_regional"
echo "   - world_tourism_data"
echo "   - brazil_ministries_data"
echo "   - world_drugs_data"
echo "   - world_religion_data"
echo "   - world_ngos"
echo "   - central_banks"
echo "   - central_banks_women_data"
echo ""
