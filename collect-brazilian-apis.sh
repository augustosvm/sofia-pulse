#!/bin/bash

################################################################################
# Sofia Pulse - Brazilian Official APIs Collection
################################################################################
#
# Coleta dados de 4 APIs oficiais brasileiras:
# 1. BACEN SGS - Indicadores macro (Selic, câmbio, inflação) - DIÁRIO
# 2. IBGE API - PIB, emprego, produção industrial - MENSAL/TRIMESTRAL
# 3. MDIC ComexStat - Import/export de produtos tech - MENSAL
# 4. IPEA - Séries históricas desde 1940s - VARIÁVEL
#
# Todas APIs são oficiais do governo brasileiro e totalmente públicas.
# Dados estruturados em JSON.
#
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env
set -a
source .env 2>/dev/null || true
set +a

echo "════════════════════════════════════════════════════════════════"
echo "🇧🇷 BRAZILIAN OFFICIAL APIs COLLECTION"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Activate venv
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
    echo "✅ Virtual environment activated"
    echo ""
fi

################################################################################
# 1. BACEN SGS API
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "📊 1. BACEN SGS API - Banco Central do Brasil"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Indicators: Selic, Dólar, IPCA, PIB, Desemprego, Reservas"
echo "Frequency: Daily (Selic, Dólar), Monthly (IPCA, PIB)"
echo "URL: https://api.bcb.gov.br/dados/serie/"
echo ""

python3 scripts/collect-bacen-sgs.py || echo "⚠️  BACEN collection failed"

echo ""
echo "⏳ Waiting 10s before next API..."
sleep 10

################################################################################
# 2. IBGE API
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 2. IBGE API - Instituto Brasileiro de Geografia e Estatística"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Indicators: PIB, IPCA, Desemprego, Produção Industrial, Renda"
echo "Frequency: Monthly/Quarterly"
echo "URL: https://servicodados.ibge.gov.br/api/"
echo ""

python3 scripts/collect-ibge-api.py || echo "⚠️  IBGE collection failed"

echo ""
echo "⏳ Waiting 10s before next API..."
sleep 10

################################################################################
# 3. MDIC ComexStat API
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 3. MDIC ComexStat API - Comércio Exterior"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  TEMPORARILY DISABLED"
echo "Reason: API endpoint changed or deprecated"
echo "Old URL: http://api.comexstat.mdic.gov.br/"
echo "Status: DNS resolution fails"
echo ""
echo "TODO: Find new ComexStat API endpoint"
echo ""

# python3 scripts/collect-mdic-comexstat.py || echo "⚠️  MDIC collection failed"

echo "⏳ Skipping to next API..."
sleep 2

################################################################################
# 4. IPEA API
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 4. IPEA API - Instituto de Pesquisa Econômica Aplicada"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Data: Historical series since 1940s (GDP, inflation, employment, income)"
echo "Frequency: Variable"
echo "URL: http://ipeadata.gov.br/api/"
echo ""

python3 scripts/collect-ipea-api.py || echo "⚠️  IPEA collection failed"

################################################################################
# SUMMARY
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ BRAZILIAN APIs COLLECTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "📊 APIs collected:"
echo "  1. ✅ BACEN SGS - 7 series (Selic, Dólar, IPCA, etc)"
echo "  2. ✅ IBGE - 6 indicators (PIB, Desemprego, Produção)"
echo "  3. ⚠️  MDIC ComexStat - DISABLED (API endpoint changed)"
echo "  4. ✅ IPEA - 10 series (historical data)"
echo ""
echo "💡 NEW INSIGHTS POSSIBLE:"
echo ""
echo "  📊 Selic vs Funding correlation"
echo "  💱 Dollar exchange rate vs Foreign investment"
echo "  📈 Sectoral GDP vs Best cities for expansion"
echo "  🚢 Tech imports vs Engineer demand"
echo "  📉 Inflation vs Tech salaries"
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "  1. Create analytics correlating Selic with Funding"
echo "  2. Create Brazil Macro Tech Index report"
echo "  3. Add to daily collection schedule"
echo ""
