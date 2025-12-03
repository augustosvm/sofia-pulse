#!/bin/bash
# ============================================================================
# Test Sofia + WhatsApp Integration
# ============================================================================

set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "============================================================================"
echo "🧪 SOFIA PULSE - TEST WHATSAPP + SOFIA INTEGRATION"
echo "============================================================================"
echo ""

# Load .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded .env"
else
    echo "⚠️  No .env file found"
fi

echo ""
echo "Configuration:"
echo "  WHATSAPP_NUMBER: ${WHATSAPP_NUMBER:-NOT SET}"
echo "  SOFIA_API_URL: ${SOFIA_API_URL:-http://localhost:8001/api/v2/chat}"
echo "  WHATSAPP_ENABLED: ${WHATSAPP_ENABLED:-true}"
echo ""

# Test 1: Check Sofia API is running
echo "Test 1: Checking Sofia API..."
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "  ✅ Sofia API is running"
else
    echo "  ❌ Sofia API not responding at http://localhost:8001"
    echo "     Start it with: docker ps | grep sofia"
    exit 1
fi

echo ""

# Test 2: Test Sofia API endpoint
echo "Test 2: Testing Sofia API chat endpoint..."
SOFIA_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v2/chat \
    -H "Content-Type: application/json" \
    -d '{
        "query": "Teste de integração. Responda com OK.",
        "user_id": "test",
        "channel": "test"
    }' 2>/dev/null || echo "{}")

if echo "$SOFIA_RESPONSE" | grep -q "response"; then
    echo "  ✅ Sofia API responding correctly"
    echo "     Response preview: $(echo $SOFIA_RESPONSE | jq -r '.response' 2>/dev/null | head -c 60)..."
else
    echo "  ❌ Sofia API not responding correctly"
    echo "     Response: $SOFIA_RESPONSE"
    exit 1
fi

echo ""

# Test 3: Test Python integration module
echo "Test 3: Testing Python integration module..."
cd "$SOFIA_DIR"

# Activate venv if exists
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
fi

python3 scripts/utils/sofia_whatsapp_integration.py
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "  ✅ Integration module working!"
else
    echo ""
    echo "  ❌ Integration module failed"
    exit 1
fi

echo ""
echo "============================================================================"
echo "✅ ALL TESTS PASSED"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Run examples: python3 scripts/example-alert-with-sofia.py"
echo "  2. Integrate with your collectors"
echo "  3. Check WhatsApp for test message"
echo ""
