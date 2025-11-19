#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔧 FIX MERGE CONFLICT AND PULL LATEST CODE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

cd /home/ubuntu/sofia-pulse

echo "1. Backing up .env.example if it exists..."
if [ -f ".env.example" ]; then
    mv .env.example .env.example.backup
    echo "   ✅ Backed up to .env.example.backup"
else
    echo "   ℹ️  No .env.example found"
fi

echo ""
echo "2. Pulling latest code..."
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE

echo ""
echo "3. Checking new files..."
ls -lh scripts/collect-electricity-consumption.py 2>/dev/null && echo "   ✅ Electricity collector" || echo "   ❌ Missing"
ls -lh scripts/collect-port-traffic.py 2>/dev/null && echo "   ✅ Port traffic collector" || echo "   ❌ Missing"
ls -lh scripts/collect-commodity-prices.py 2>/dev/null && echo "   ✅ Commodity prices collector" || echo "   ❌ Missing"
ls -lh scripts/collect-semiconductor-sales.py 2>/dev/null && echo "   ✅ Semiconductor sales collector" || echo "   ❌ Missing"
ls -lh test-apis.py 2>/dev/null && echo "   ✅ API test script" || echo "   ❌ Missing"
ls -lh API_SETUP.md 2>/dev/null && echo "   ✅ API setup guide" || echo "   ❌ Missing"

echo ""
echo "4. Creating new database tables..."
source venv-analytics/bin/activate
python3 create-tables-python.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ MERGE FIXED AND CODE UPDATED!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Next steps:"
echo "   1. Test API keys: python3 test-apis.py"
echo "   2. Test collectors:"
echo "      python3 scripts/collect-electricity-consumption.py"
echo "      python3 scripts/collect-port-traffic.py"
echo "      python3 scripts/collect-commodity-prices.py"
echo "      python3 scripts/collect-semiconductor-sales.py"
echo "   3. Run full pipeline: bash run-all-now.sh"
echo ""
