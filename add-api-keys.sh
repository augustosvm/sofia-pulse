#!/bin/bash

################################################################################
# Add API Keys to .env (BEA + Kaggle + FRED)
################################################################################

set -e

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

# API Keys
BEA_KEY="D1353E8E-038E-474D-BB08-CDC6CA54775A"
KAGGLE_USERNAME="augustovespermann"
KAGGLE_KEY="ce3f5edfc3f96a5c122ef71a02d7454f"
FRED_KEY="5d314a9df72825b22703adcf1a03180a"

echo "════════════════════════════════════════════════════════════════"
echo "🔑 Adding API Keys to .env"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 BEA API (Bureau of Economic Analysis)"
echo "   Key: $BEA_KEY"
echo ""
echo "📊 Kaggle API (Datasets & Competitions)"
echo "   Username: $KAGGLE_USERNAME"
echo "   Key: $KAGGLE_KEY"
echo ""
echo "📊 FRED API (Federal Reserve Economic Data)"
echo "   Key: $FRED_KEY"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
fi

# Add/Update BEA API Key
if grep -q "^BEA_API_KEY=" .env; then
    echo "⚠️  BEA_API_KEY already exists - updating..."
    sed -i "s/^BEA_API_KEY=.*/BEA_API_KEY=$BEA_KEY/" .env
else
    echo "➕ Adding BEA_API_KEY..."
    echo "" >> .env
    echo "# BEA API (Bureau of Economic Analysis)" >> .env
    echo "BEA_API_KEY=$BEA_KEY" >> .env
fi
echo "   ✅ BEA_API_KEY configured"

# Add/Update Kaggle API
if grep -q "^KAGGLE_USERNAME=" .env; then
    echo "⚠️  Kaggle credentials already exist - updating..."
    sed -i "s/^KAGGLE_USERNAME=.*/KAGGLE_USERNAME=$KAGGLE_USERNAME/" .env
    sed -i "s/^KAGGLE_KEY=.*/KAGGLE_KEY=$KAGGLE_KEY/" .env
else
    echo "➕ Adding Kaggle credentials..."
    echo "" >> .env
    echo "# Kaggle API (Datasets & Competitions)" >> .env
    echo "KAGGLE_USERNAME=$KAGGLE_USERNAME" >> .env
    echo "KAGGLE_KEY=$KAGGLE_KEY" >> .env
fi
echo "   ✅ Kaggle credentials configured"

# Add/Update FRED API Key
if grep -q "^FRED_API_KEY=" .env; then
    echo "⚠️  FRED_API_KEY already exists - updating..."
    sed -i "s/^FRED_API_KEY=.*/FRED_API_KEY=$FRED_KEY/" .env
else
    echo "➕ Adding FRED_API_KEY..."
    echo "" >> .env
    echo "# FRED API (Federal Reserve Economic Data)" >> .env
    echo "FRED_API_KEY=$FRED_KEY" >> .env
fi
echo "   ✅ FRED_API_KEY configured"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ API Keys added successfully!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Available APIs:"
echo "   • BEA: U.S. economic data (GDP, trade, industry)"
echo "   • Kaggle: 50,000+ datasets, competitions, notebooks"
echo "   • FRED: Federal Reserve economic data (500,000+ time series)"
echo ""
echo "🔧 Next steps:"
echo "   1. Create collectors to use these APIs"
echo "   2. Run: bash RUN-EVERYTHING-COMPLETE.sh"
echo ""
