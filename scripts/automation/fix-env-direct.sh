#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔧 DIRECT FIX: Add API Keys to .env"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

cd /home/ubuntu/sofia-pulse

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backed up current .env"

# Check if keys already exist with values
if grep -q "^EIA_API_KEY=QKUixUcUGW" .env && grep -q "^API_NINJAS_KEY=IsggR55vW5" .env; then
    echo "✅ Both API keys already configured correctly!"
    echo ""
    echo "   EIA_API_KEY: $(grep '^EIA_API_KEY=' .env | cut -d= -f2 | cut -c1-15)..."
    echo "   API_NINJAS_KEY: $(grep '^API_NINJAS_KEY=' .env | cut -d= -f2 | cut -c1-15)..."
    echo ""
    echo "Run: python3 test-apis.py"
    exit 0
fi

echo "🔑 Adding/Updating API keys..."
echo ""

# Create temporary file with updated keys
cat .env | \
    sed 's|^EIA_API_KEY=.*|EIA_API_KEY=QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys|' | \
    sed 's|^API_NINJAS_KEY=.*|API_NINJAS_KEY=IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I|' \
    > .env.tmp

# Replace original
mv .env.tmp .env

echo "✅ Updated .env file"
echo ""

# Verify
echo "🧪 Verifying..."
if grep -q "^EIA_API_KEY=QKUixUcUGW" .env && grep -q "^API_NINJAS_KEY=IsggR55vW5" .env; then
    echo "✅ API keys configured successfully!"
    echo ""
    echo "   EIA_API_KEY: $(grep '^EIA_API_KEY=' .env | cut -d= -f2 | cut -c1-15)..."
    echo "   API_NINJAS_KEY: $(grep '^API_NINJAS_KEY=' .env | cut -d= -f2 | cut -c1-15)..."
else
    echo "❌ Keys not found. Manual check required:"
    echo ""
    echo "Run these commands:"
    echo ""
    echo "cat >> .env << 'EOF'"
    echo ""
    echo "# API Keys"
    echo "EIA_API_KEY=QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys"
    echo "API_NINJAS_KEY=IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I"
    echo "EOF"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ DONE!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next: python3 test-apis.py"
echo ""
