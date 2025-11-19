#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 RUN ALL COLLECTORS WITH VENV"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Detect environment
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
elif [ -d "/home/user/sofia-pulse" ]; then
    SOFIA_DIR="/home/user/sofia-pulse"
else
    echo "❌ Sofia Pulse directory not found!"
    exit 1
fi

cd "$SOFIA_DIR"

# Activate venv
if [ -d "venv-analytics" ]; then
    echo "✅ Activating venv-analytics..."
    source venv-analytics/bin/activate
else
    echo "❌ venv-analytics not found! Run ./install-python-deps.sh first"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🧪 TESTING APIS"
echo "════════════════════════════════════════════════════════════════════════════════"
python3 test-apis.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 CREATING TABLES"
echo "════════════════════════════════════════════════════════════════════════════════"
python3 create-tables-python.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 RUNNING COLLECTORS"
echo "════════════════════════════════════════════════════════════════════════════════"

echo ""
echo "⚡ Electricity Consumption..."
python3 scripts/collect-electricity-consumption.py

echo ""
echo "🚢 Port Traffic..."
python3 scripts/collect-port-traffic.py

echo ""
echo "📈 Commodity Prices (API NINJAS)..."
python3 scripts/collect-commodity-prices.py

echo ""
echo "💾 Semiconductor Sales..."
python3 scripts/collect-semiconductor-sales.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ ALL COLLECTORS COMPLETED!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "💡 Check if commodity_prices shows REAL prices (not placeholder)"
echo ""
