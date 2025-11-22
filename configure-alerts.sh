#!/bin/bash
################################################################################
# SOFIA PULSE - CONFIGURE ALERTS
# Configures WhatsApp alerts via sofia-mastra-rag
################################################################################

ENV_FILE=".env"

echo "════════════════════════════════════════════════════════════════"
echo "📱 SOFIA PULSE - CONFIGURE ALERTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# WhatsApp number
WHATSAPP_NUMBER="5527988024062"  # +55 27 98802-4062

# Sofia API endpoint (local)
SOFIA_API_ENDPOINT="http://localhost:8001/api/v2/chat"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

echo "📝 Configuring WhatsApp alerts..."
echo "   Number: +$WHATSAPP_NUMBER"
echo "   Endpoint: $SOFIA_API_ENDPOINT"
echo ""

# Add/update WhatsApp configuration
if grep -q "^WHATSAPP_NUMBER=" "$ENV_FILE"; then
    sed -i "s|^WHATSAPP_NUMBER=.*|WHATSAPP_NUMBER=$WHATSAPP_NUMBER|" "$ENV_FILE"
    echo "✅ Updated WHATSAPP_NUMBER"
else
    echo "" >> "$ENV_FILE"
    echo "# WhatsApp Alerts Configuration" >> "$ENV_FILE"
    echo "WHATSAPP_NUMBER=$WHATSAPP_NUMBER" >> "$ENV_FILE"
    echo "✅ Added WHATSAPP_NUMBER"
fi

if grep -q "^SOFIA_API_ENDPOINT=" "$ENV_FILE"; then
    sed -i "s|^SOFIA_API_ENDPOINT=.*|SOFIA_API_ENDPOINT=$SOFIA_API_ENDPOINT|" "$ENV_FILE"
    echo "✅ Updated SOFIA_API_ENDPOINT"
else
    echo "SOFIA_API_ENDPOINT=$SOFIA_API_ENDPOINT" >> "$ENV_FILE"
    echo "✅ Added SOFIA_API_ENDPOINT"
fi

if grep -q "^ALERT_WHATSAPP_ENABLED=" "$ENV_FILE"; then
    sed -i "s|^ALERT_WHATSAPP_ENABLED=.*|ALERT_WHATSAPP_ENABLED=true|" "$ENV_FILE"
    echo "✅ Updated ALERT_WHATSAPP_ENABLED"
else
    echo "ALERT_WHATSAPP_ENABLED=true" >> "$ENV_FILE"
    echo "✅ Added ALERT_WHATSAPP_ENABLED"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ALERTS CONFIGURED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
grep -E "WHATSAPP_|SOFIA_API_|ALERT_WHATSAPP" "$ENV_FILE"
echo ""
echo "Test alerts with:"
echo "  python3 scripts/test-alerts.py"
echo ""
echo "════════════════════════════════════════════════════════════════"
