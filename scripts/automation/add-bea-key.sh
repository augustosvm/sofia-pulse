#!/bin/bash

################################################################################
# Add BEA API Key to .env
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

BEA_KEY="D1353E8E-038E-474D-BB08-CDC6CA54775A"

echo "════════════════════════════════════════════════════════════════"
echo "🔑 Adding BEA API Key"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 BEA = Bureau of Economic Analysis (U.S. Department of Commerce)"
echo "🔑 Key: $BEA_KEY"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
fi

# Check if key already exists
if grep -q "BEA_API_KEY" .env; then
    echo "⚠️  BEA_API_KEY already exists in .env"
    echo "   Updating value..."
    sed -i "s/BEA_API_KEY=.*/BEA_API_KEY=$BEA_KEY/" .env
else
    echo "➕ Adding BEA_API_KEY to .env..."
    echo "" >> .env
    echo "# BEA API (Bureau of Economic Analysis)" >> .env
    echo "BEA_API_KEY=$BEA_KEY" >> .env
fi

echo "✅ BEA API Key added successfully!"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📝 You can now use BEA data in collectors"
echo "════════════════════════════════════════════════════════════════"
echo ""
