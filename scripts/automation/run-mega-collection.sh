#!/bin/bash
# ============================================================================
# SOFIA PULSE - MEGA COLLECTION (ALL DATA SOURCES)
# ============================================================================
# Executa TODOS os collectors (Node.js + Python)
# Tempo estimado: 15-20 minutos
# ============================================================================

set -e  # Exit on error

# Fix Node.js 18 + undici compatibility - Load polyfill FIRST!
export NODE_OPTIONS="--require $(pwd)/node-polyfill.cjs"

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "============================================================================"
echo "🚀 SOFIA PULSE - MEGA COLLECTION"
echo "============================================================================"
echo ""
echo "⏱️  Tempo estimado: 15-20 minutos"
echo "📊 Coletará dados de 30+ fontes"
echo ""

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# ============================================================================
# PHASE 1: PYTHON COLLECTORS (5 collectors)
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "📊 PHASE 1: PYTHON COLLECTORS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

if [ ! -d "venv-analytics" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv-analytics
fi

source venv-analytics/bin/activate

echo "1️⃣  Electricity Consumption (EIA API + OWID)"
python3 scripts/collect-electricity-consumption.py || echo "⚠️  Skipped"
echo ""

echo "2️⃣  Port Traffic (World Bank TEUs)"
python3 scripts/collect-port-traffic.py || echo "⚠️  Skipped"
echo ""

echo "3️⃣  Commodity Prices (API Ninjas)"
python3 scripts/collect-commodity-prices.py || echo "⚠️  Skipped"
echo ""

echo "4️⃣  Semiconductor Sales (WSTS/SIA)"
python3 scripts/collect-semiconductor-sales.py || echo "⚠️  Skipped"
echo ""

echo "5️⃣  Socioeconomic Indicators (World Bank - 56 indicators)"
python3 scripts/collect-socioeconomic-indicators.py || echo "⚠️  Skipped"
echo ""

echo "6️⃣  Global Energy Data (Our World in Data)"
python3 scripts/collect-energy-global.py || echo "⚠️  Skipped"
echo ""

echo "✅ Python collectors complete!"
echo ""

# ============================================================================
# PHASE 2: NODE.JS COLLECTORS (20+ collectors)
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "📡 PHASE 2: NODE.JS COLLECTORS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "⚠️  Node modules not found. Installing..."
    npm install
    echo ""
fi

# Tech Trends
echo "🔹 Tech Trends & Open Source"
npx tsx scripts/collect-github-trending.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-github-niches.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-hackernews.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-reddit-tech.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-npm-stats.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-pypi-stats.ts || echo "⚠️  Skipped"
echo ""

# Research & Academia
echo "🔹 Research & Academia"
npx tsx scripts/collect-arxiv-ai.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-openalex.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-asia-universities.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-nih-grants.ts || echo "⚠️  Skipped"
echo ""

# Funding & Finance
echo "🔹 Funding & Finance"
npx tsx finance/scripts/collect-funding-rounds.ts || echo "⚠️  Skipped"
npx tsx finance/scripts/collect-brazil-stocks.ts || echo "⚠️  Skipped"
npx tsx finance/scripts/collect-nasdaq-momentum.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-hkex-ipos.ts || echo "⚠️  Skipped"
npx tsx collectors/ipo-calendar.ts || echo "⚠️  Skipped"
echo ""

# Patents
echo "🔹 Patents"
npx tsx scripts/collect-epo-patents.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-wipo-china-patents.ts || echo "⚠️  Skipped"
echo ""

# Critical Sectors (NEW!)
echo "🔹 Critical Sectors"
npx tsx scripts/collect-cybersecurity.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-space-industry.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-ai-regulation.ts || echo "⚠️  Skipped"
echo ""

# Geopolitics
echo "🔹 Geopolitics"
npx tsx scripts/collect-gdelt.ts || echo "⚠️  Skipped"
echo ""

# Industry Specific
echo "🔹 Industry Specific"
npx tsx scripts/collect-cardboard-production.ts || echo "⚠️  Skipped"
npx tsx scripts/collect-ai-companies.ts || echo "⚠️  Skipped"
echo ""

echo "✅ Node.js collectors complete!"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ COLLECTION COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Data Sources Collected:"
echo ""
echo "   Python Collectors (6):"
echo "   • Electricity consumption (239 countries)"
echo "   • Port traffic (World Bank TEUs)"
echo "   • Commodity prices (18+ commodities)"
echo "   • Semiconductor sales (global)"
echo "   • Socioeconomic indicators (56 indicators, 200+ countries)"
echo "   • Global energy data (renewables, capacity)"
echo ""
echo "   Node.js Collectors (20+):"
echo "   • GitHub Trending (53 languages)"
echo "   • HackerNews (top stories)"
echo "   • Reddit Tech (6 subreddits)"
echo "   • NPM Stats (30+ packages)"
echo "   • PyPI Stats (26+ packages)"
echo "   • ArXiv AI Papers"
echo "   • OpenAlex Research"
echo "   • Asia Universities"
echo "   • NIH Grants"
echo "   • Funding Rounds"
echo "   • B3, NASDAQ, HKEX Stocks"
echo "   • IPO Calendar"
echo "   • EPO, WIPO Patents"
echo "   • Cybersecurity (CVEs, Breaches)"
echo "   • Space Industry (Launches)"
echo "   • AI Regulation (Laws, Policies)"
echo "   • GDELT (Geopolitical Events)"
echo "   • Cardboard Production"
echo "   • AI Companies"
echo ""
echo "📈 Total Records: ~150,000+"
echo "🗄️  Database: sofia_db"
echo ""
echo "🎯 Next Step: Run analytics with run-mega-analytics.sh"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
