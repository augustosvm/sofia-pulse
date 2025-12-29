#!/bin/bash

################################################################################
# Sofia Pulse - Fast APIs Collection
################################################################################
#
# Coleta dados de APIs SEM rate limit severo ou com alto limite
# Executa: 07:00 BRT / 10:00 UTC
#
# APIs incluídas:
# - Python collectors (World Bank, EIA, OWID - sem rate limit)
# - HackerNews (sem rate limit)
# - NPM/PyPI (limite alto)
#
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📊 SOFIA PULSE - FAST APIs COLLECTION"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "📡 Collecting from APIs without severe rate limits"
echo ""

# Activate Python venv if exists
if [ -d "venv-analytics" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv-analytics/bin/activate
fi

################################################################################
# PYTHON COLLECTORS (No rate limit)
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "🐍 PYTHON COLLECTORS"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Electricity Consumption (EIA API + OWID)..."
python3 scripts/collect-electricity-consumption.py || echo "⚠️  Failed"

echo ""
echo "2️⃣  Port Traffic (World Bank)..."
python3 scripts/collect-port-traffic.py || echo "⚠️  Failed"

echo ""
echo "3️⃣  Commodity Prices (API Ninjas)..."
python3 scripts/collect-commodity-prices.py || echo "⚠️  Failed"

echo ""
echo "4️⃣  Semiconductor Sales (SIA)..."
python3 scripts/collect-semiconductor-sales.py || echo "⚠️  Failed"

echo ""
echo "5️⃣  Socioeconomic Indicators (World Bank - 56 indicators)..."
python3 scripts/collect-socioeconomic-indicators.py || echo "⚠️  Failed"

echo ""
echo "6️⃣  Global Energy Data (OWID)..."
python3 scripts/collect-energy-global.py || echo "⚠️  Failed"

################################################################################
# NODE.JS COLLECTORS (High limit or no limit)
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📡 NODE.JS COLLECTORS (High Limit)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "7️⃣  HackerNews (No rate limit)..."
npx tsx scripts/collect-hackernews.ts || echo "⚠️  Failed"

echo ""
echo "8️⃣  NPM Stats (High limit)..."
npx tsx scripts/collect-npm-stats.ts || echo "⚠️  Failed"

echo ""
echo "9️⃣  PyPI Stats (High limit)..."
npx tsx scripts/collect-pypi-stats.ts || echo "⚠️  Failed"

echo ""
echo "🔟 ArXiv AI Papers (Free API)..."
npx tsx scripts/collect-arxiv-ai.ts || echo "⚠️  Failed"

echo ""
echo "1️⃣1️⃣  Space Industry (Free API)..."
npx tsx scripts/collect-space-industry.ts || echo "⚠️  Failed"

echo ""
echo "1️⃣2️⃣  Cybersecurity (NVD API)..."
npx tsx scripts/collect-cybersecurity.ts || echo "⚠️  Failed"

################################################################################
# SUMMARY
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ FAST APIs COLLECTION COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "📊 Collectors Run: 12"
echo "📡 APIs with NO severe rate limits"
echo ""
echo "🎯 Next Step: Run limited APIs collection at 16:00 UTC"
echo ""
