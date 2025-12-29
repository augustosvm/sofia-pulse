#!/bin/bash
# ============================================================================
# Setup WhatsApp Configuration
# ============================================================================

set -e

echo "============================================================================"
echo "⚙️  SOFIA PULSE - WHATSAPP CONFIGURATION SETUP"
echo "============================================================================"
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted. Keeping existing .env"
        exit 0
    fi
fi

# Copy from example
if [ ! -f ".env.example" ]; then
    echo "❌ .env.example not found"
    exit 1
fi

echo "📋 Creating .env from .env.example..."
cp .env.example .env
echo "✅ .env created"
echo ""

# Prompt for WhatsApp configuration
echo "============================================================================"
echo "📱 WHATSAPP CONFIGURATION"
echo "============================================================================"
echo ""
echo "Por favor, forneça suas configurações:"
echo ""

# WhatsApp number
while true; do
    read -p "Seu número WhatsApp (ex: 5527988024062): " WHATSAPP_NUM
    if [ -n "$WHATSAPP_NUM" ]; then
        break
    fi
    echo "❌ Número não pode ser vazio"
done

# Business number (optional)
read -p "Número Business (enter para usar mesmo número): " WHATSAPP_SENDER
if [ -z "$WHATSAPP_SENDER" ]; then
    WHATSAPP_SENDER="$WHATSAPP_NUM"
fi

# Update .env file
echo ""
echo "✍️  Updating .env file..."

# Add WhatsApp config if not exists
if ! grep -q "WHATSAPP_NUMBER=" .env; then
    cat >> .env << EOF

# ============================================================================
# WhatsApp Configuration (Added by setup)
# ============================================================================
WHATSAPP_NUMBER=$WHATSAPP_NUM
WHATSAPP_SENDER=$WHATSAPP_SENDER
SOFIA_API_URL=http://localhost:8001/api/v2/chat
WHATSAPP_ENABLED=true
EOF
else
    # Update existing values
    sed -i "s/WHATSAPP_NUMBER=.*/WHATSAPP_NUMBER=$WHATSAPP_NUM/" .env
    sed -i "s/WHATSAPP_SENDER=.*/WHATSAPP_SENDER=$WHATSAPP_SENDER/" .env
fi

echo "✅ .env file updated"
echo ""

# Show configuration
echo "============================================================================"
echo "✅ CONFIGURATION SAVED"
echo "============================================================================"
echo ""
echo "Your WhatsApp configuration:"
echo "  • WHATSAPP_NUMBER: $WHATSAPP_NUM"
echo "  • WHATSAPP_SENDER: $WHATSAPP_SENDER"
echo "  • SOFIA_API_URL: http://localhost:8001/api/v2/chat"
echo "  • WHATSAPP_ENABLED: true"
echo ""

# Test configuration
echo "============================================================================"
echo "🧪 TESTING CONFIGURATION"
echo "============================================================================"
echo ""

# Test if Sofia API is running
echo "1️⃣  Checking Sofia API..."
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✅ Sofia API is running"
else
    echo "   ⚠️  Sofia API not responding"
    echo "   Start with: docker restart sofia-mastra-api"
fi

echo ""

# Test Python script can load env
echo "2️⃣  Testing Python can load .env..."
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
fi

python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
num = os.getenv('WHATSAPP_NUMBER', 'NOT_SET')
if num != 'NOT_SET' and num != 'YOUR_WHATSAPP_NUMBER':
    print('   ✅ Python can load WHATSAPP_NUMBER:', num)
    exit(0)
else:
    print('   ❌ Python cannot load WHATSAPP_NUMBER')
    print('   Got:', num)
    exit(1)
" 2>/dev/null

PYTHON_TEST=$?

echo ""

# Install python-dotenv if needed
if [ $PYTHON_TEST -ne 0 ]; then
    echo "📦 Installing python-dotenv..."
    pip install python-dotenv > /dev/null 2>&1 || true
fi

echo "============================================================================"
echo "✅ SETUP COMPLETE"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Test integration: bash test-sofia-whatsapp.sh"
echo "  2. Send test alert: python3 scripts/example-alert-with-sofia.py"
echo "  3. Check your WhatsApp for messages"
echo ""
echo "Configuration file: $(pwd)/.env"
echo ""
