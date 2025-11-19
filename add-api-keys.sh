#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔧 FIX: Add API Keys to .env"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

cd /home/ubuntu/sofia-pulse

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Creating from .env.example..."
    cp .env.example .env
fi

# Check if keys are already present
if grep -q "EIA_API_KEY=QKUixUcUGW" .env 2>/dev/null; then
    echo "✅ EIA_API_KEY already configured"
else
    echo "🔑 Adding EIA_API_KEY..."
    # Replace empty EIA_API_KEY with actual key
    sed -i 's|^EIA_API_KEY=$|EIA_API_KEY=QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys|' .env
    echo "   ✅ Added EIA_API_KEY"
fi

if grep -q "API_NINJAS_KEY=IsggR55vW5" .env 2>/dev/null; then
    echo "✅ API_NINJAS_KEY already configured"
else
    echo "🔑 Adding API_NINJAS_KEY..."
    # Check if API_NINJAS_KEY line exists
    if grep -q "^API_NINJAS_KEY=" .env; then
        # Replace existing empty value
        sed -i 's|^API_NINJAS_KEY=$|API_NINJAS_KEY=IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I|' .env
    else
        # Add new line after EIA_API_KEY
        sed -i '/^EIA_API_KEY=/a\\n# API Ninjas for commodity prices (oil, gold, copper, wheat, etc)\n# Get your free key: https://api-ninjas.com/\nAPI_NINJAS_KEY=IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I' .env
    fi
    echo "   ✅ Added API_NINJAS_KEY"
fi

echo ""
echo "🧪 Verifying configuration..."
echo ""

if grep -q "EIA_API_KEY=QKUixUcUGW" .env && grep -q "API_NINJAS_KEY=IsggR55vW5" .env; then
    echo "✅ Both API keys configured!"
    echo ""
    echo "   EIA_API_KEY: $(grep EIA_API_KEY .env | cut -d= -f2 | cut -c1-15)..."
    echo "   API_NINJAS_KEY: $(grep API_NINJAS_KEY .env | tail -1 | cut -d= -f2 | cut -c1-15)..."
else
    echo "⚠️  Some keys may be missing. Check .env manually"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ API KEYS CONFIGURED!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo "   1. Test: python3 test-apis.py"
echo "   2. Run collectors again"
echo ""
