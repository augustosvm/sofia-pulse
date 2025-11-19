#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔑 SETUP API KEYS - DEFINITIVE FIX"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Define the API keys
EIA_KEY="QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys"
NINJAS_KEY="IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I"

# Detect environment (server or local)
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
    echo "📍 Detected server environment: $SOFIA_DIR"
elif [ -d "/home/user/sofia-pulse" ]; then
    SOFIA_DIR="/home/user/sofia-pulse"
    echo "📍 Detected local environment: $SOFIA_DIR"
else
    echo "❌ Sofia Pulse directory not found!"
    exit 1
fi

cd "$SOFIA_DIR"
echo ""

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📄 Creating .env from .env.example..."
        cp .env.example .env
        echo "✅ Created .env"
    else
        echo "❌ .env.example not found! Creating minimal .env..."
        cat > .env << 'EOF'
# PostgreSQL Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=sofia_db

# API Keys
EOF
        echo "✅ Created minimal .env"
    fi
else
    echo "✅ Found existing .env"
    # Backup
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Created backup"
fi

echo ""
echo "🔧 Configuring API keys..."
echo ""

# Remove old API key lines if they exist
sed -i '/^EIA_API_KEY=/d' .env 2>/dev/null || true
sed -i '/^API_NINJAS_KEY=/d' .env 2>/dev/null || true

# Add the API keys
echo "" >> .env
echo "# API Keys - Added by setup-api-keys-final.sh" >> .env
echo "EIA_API_KEY=$EIA_KEY" >> .env
echo "API_NINJAS_KEY=$NINJAS_KEY" >> .env

echo "✅ API keys added to .env"
echo ""

# Verify
echo "🧪 Verifying configuration..."
echo ""

if grep -q "^EIA_API_KEY=$EIA_KEY" .env; then
    echo "   ✅ EIA_API_KEY: ${EIA_KEY:0:15}..."
else
    echo "   ❌ EIA_API_KEY verification failed!"
    exit 1
fi

if grep -q "^API_NINJAS_KEY=$NINJAS_KEY" .env; then
    echo "   ✅ API_NINJAS_KEY: ${NINJAS_KEY:0:15}..."
else
    echo "   ❌ API_NINJAS_KEY verification failed!"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ SUCCESS! API Keys Configured"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo ""
echo "   1. Test APIs:  python3 test-apis.py"
echo "   2. Run collector: python3 scripts/collect-commodity-prices.py"
echo ""
echo "💡 Your .env file is at: $SOFIA_DIR/.env"
echo ""
