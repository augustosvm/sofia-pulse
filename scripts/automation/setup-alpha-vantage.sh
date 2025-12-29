#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔑 SETUP ALPHA VANTAGE API KEY"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

ALPHA_KEY="JFVYRODTWGO1W5M6"

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

echo "📍 Working directory: $SOFIA_DIR"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env not found! Run setup-api-keys-final.sh first"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Created backup"
echo ""

# Remove old Alpha Vantage key if exists
sed -i '/^ALPHA_VANTAGE_API_KEY=/d' .env 2>/dev/null || true

# Add new key
echo "" >> .env
echo "# Alpha Vantage API - For commodities and financial data" >> .env
echo "ALPHA_VANTAGE_API_KEY=$ALPHA_KEY" >> .env

echo "✅ Alpha Vantage API key added"
echo ""

# Verify
if grep -q "^ALPHA_VANTAGE_API_KEY=$ALPHA_KEY" .env; then
    echo "🧪 Verification: ✅ ALPHA_VANTAGE_API_KEY: ${ALPHA_KEY:0:15}..."
else
    echo "❌ Verification failed!"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ SUCCESS! Alpha Vantage Configured"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Your .env now has 3 API keys:"
echo "   ✅ EIA_API_KEY (electricity data)"
echo "   ✅ API_NINJAS_KEY (platinum price)"
echo "   ✅ ALPHA_VANTAGE_API_KEY (commodities - NOVO!)"
echo ""
echo "💡 Next steps:"
echo "   1. Test: python3 test-apis.py"
echo "   2. Update crontab: ./update-crontab-complete.sh"
echo ""
