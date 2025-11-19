#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔑 TESTANDO API KEYS"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

cd /home/user/sofia-pulse
source .env 2>/dev/null || true

echo "1. Testing EIA API..."
if [ -n "$EIA_API_KEY" ]; then
    echo "   ✅ EIA_API_KEY configurada: ${EIA_API_KEY:0:10}..."

    # Test EIA API
    RESPONSE=$(curl -s "https://api.eia.gov/v2/international/data/?api_key=$EIA_API_KEY&frequency=annual&data[0]=value&facets[activityId][]=2&length=1" || echo "ERROR")

    if echo "$RESPONSE" | grep -q '"response"'; then
        echo "   ✅ EIA API funcionando!"
    else
        echo "   ❌ EIA API falhou"
        echo "   Response: $RESPONSE"
    fi
else
    echo "   ❌ EIA_API_KEY não encontrada"
fi

echo ""
echo "2. Testing API Ninjas..."
if [ -n "$API_NINJAS_KEY" ]; then
    echo "   ✅ API_NINJAS_KEY configurada: ${API_NINJAS_KEY:0:10}..."

    # Test API Ninjas
    RESPONSE=$(curl -s -H "X-Api-Key: $API_NINJAS_KEY" "https://api.api-ninjas.com/v1/commodityprice?name=gold" || echo "ERROR")

    if echo "$RESPONSE" | grep -q '"price"'; then
        PRICE=$(echo "$RESPONSE" | grep -o '"price":[^,}]*' | cut -d: -f2)
        echo "   ✅ API Ninjas funcionando! (Gold: \$$PRICE)"
    else
        echo "   ❌ API Ninjas falhou"
        echo "   Response: $RESPONSE"
    fi
else
    echo "   ❌ API_NINJAS_KEY não encontrada"
fi

echo ""
echo "3. Testing World Bank API (no key required)..."
RESPONSE=$(curl -s "https://api.worldbank.org/v2/country/USA/indicator/IS.SHP.GOOD.TU?format=json&per_page=1" || echo "ERROR")

if echo "$RESPONSE" | grep -q '"value"'; then
    echo "   ✅ World Bank API funcionando!"
else
    echo "   ⚠️  World Bank API resposta inesperada"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ TESTES CONCLUÍDOS"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
