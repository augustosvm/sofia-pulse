#!/bin/bash
################################################################################
# SOFIA PULSE - UPDATE WHATSAPP CONFIGURATION
# Updates WhatsApp recipient number in .env
################################################################################

ENV_FILE=".env"

echo "════════════════════════════════════════════════════════════════"
echo "📱 SOFIA PULSE - UPDATE WHATSAPP CONFIG"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Numbers
WHATSAPP_RECIPIENT="5527988024062"    # Seu número pessoal (RECEBE mensagens)
WHATSAPP_SENDER="551151990773"        # Número Business (ENVIA mensagens)
SOFIA_API_ENDPOINT="http://localhost:8001/api/v2/chat"

echo "📝 Configurando WhatsApp..."
echo ""
echo "   Sender (Business): +$WHATSAPP_SENDER (11 5199-0773)"
echo "   Recipient (Você): +$WHATSAPP_RECIPIENT (27 98802-4062)"
echo "   API Endpoint: $SOFIA_API_ENDPOINT"
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Update/add configurations
echo "Atualizando .env..."

# WHATSAPP_NUMBER (recipient - seu número)
if grep -q "^WHATSAPP_NUMBER=" "$ENV_FILE"; then
    sed -i "s|^WHATSAPP_NUMBER=.*|WHATSAPP_NUMBER=$WHATSAPP_RECIPIENT|" "$ENV_FILE"
    echo "✅ Updated WHATSAPP_NUMBER (recipient)"
else
    echo "" >> "$ENV_FILE"
    echo "# WhatsApp Configuration" >> "$ENV_FILE"
    echo "WHATSAPP_NUMBER=$WHATSAPP_RECIPIENT  # Recipient (your personal number)" >> "$ENV_FILE"
    echo "✅ Added WHATSAPP_NUMBER (recipient)"
fi

# WHATSAPP_SENDER (business number)
if grep -q "^WHATSAPP_SENDER=" "$ENV_FILE"; then
    sed -i "s|^WHATSAPP_SENDER=.*|WHATSAPP_SENDER=$WHATSAPP_SENDER|" "$ENV_FILE"
    echo "✅ Updated WHATSAPP_SENDER (business)"
else
    echo "WHATSAPP_SENDER=$WHATSAPP_SENDER  # Sender (WhatsApp Business number)" >> "$ENV_FILE"
    echo "✅ Added WHATSAPP_SENDER (business)"
fi

# SOFIA_API_ENDPOINT
if grep -q "^SOFIA_API_ENDPOINT=" "$ENV_FILE"; then
    sed -i "s|^SOFIA_API_ENDPOINT=.*|SOFIA_API_ENDPOINT=$SOFIA_API_ENDPOINT|" "$ENV_FILE"
    echo "✅ Updated SOFIA_API_ENDPOINT"
else
    echo "SOFIA_API_ENDPOINT=$SOFIA_API_ENDPOINT" >> "$ENV_FILE"
    echo "✅ Added SOFIA_API_ENDPOINT"
fi

# Enable alerts
if grep -q "^ALERT_WHATSAPP_ENABLED=" "$ENV_FILE"; then
    sed -i "s|^ALERT_WHATSAPP_ENABLED=.*|ALERT_WHATSAPP_ENABLED=true|" "$ENV_FILE"
    echo "✅ Updated ALERT_WHATSAPP_ENABLED"
else
    echo "ALERT_WHATSAPP_ENABLED=true" >> "$ENV_FILE"
    echo "✅ Added ALERT_WHATSAPP_ENABLED"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ WHATSAPP CONFIGURATION UPDATED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Current configuration in .env:"
grep -E "WHATSAPP_|SOFIA_API_|ALERT_WHATSAPP" "$ENV_FILE"
echo ""
echo "How it works:"
echo "  📤 Messages SENT FROM: +55 11 5199-0773 (WhatsApp Business)"
echo "  📥 Messages RECEIVED BY: +55 27 98802-4062 (Your personal number)"
echo ""
echo "Test WhatsApp integration:"
echo "  python3 scripts/test-whatsapp-api.py"
echo ""
echo "════════════════════════════════════════════════════════════════"
