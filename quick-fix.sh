#!/bin/bash
# Quick Fix Script - Apply all corrections at once
# Run this on the server: bash quick-fix.sh

set -e

echo "🔧 Sofia Pulse - Aplicando Correções Rápidas"
echo "=============================================="
echo ""

cd /home/ubuntu/sofia-pulse

# 1. Fix python -> python3 in python-bridge-collector.ts
echo "1️⃣ Corrigindo Python Bridge (python -> python3)..."
sed -i "s/spawn('python'/spawn('python3'/g" scripts/collectors/python-bridge-collector.ts
echo "   ✅ Python3 configurado"

# 2. Remove CISA from collectors list (blocked)
echo "2️⃣ Removendo CISA (bloqueado)..."
if [ -f "run-collectors-with-notifications.sh" ]; then
    sed -i '/^[[:space:]]*"cisa"/d' run-collectors-with-notifications.sh
    echo "   ✅ CISA removido"
else
    echo "   ⚠️ Arquivo não encontrado, pulando..."
fi

# 3. Verify .env has WhatsApp configured
echo "3️⃣ Verificando configuração WhatsApp..."
if grep -q "WHATSAPP_NUMBER=5527988024062" .env; then
    echo "   ✅ WhatsApp já configurado"
else
    echo "   ⚠️ Adicionando configuração WhatsApp..."
    cat >> .env << 'EOF'

# WhatsApp Configuration
WHATSAPP_NUMBER=5527988024062
WHATSAPP_ENABLED=true
WHATSAPP_API_URL=http://91.98.158.19:3001/send
EOF
    echo "   ✅ WhatsApp configurado"
fi

# 4. Install python-dotenv if missing
echo "4️⃣ Instalando python-dotenv..."
pip3 install python-dotenv --quiet 2>/dev/null || echo "   ⚠️ Já instalado ou erro (ignorar)"

# 5. Test collectors
echo ""
echo "🧪 Testando Collectors Corrigidos..."
echo "===================================="

echo "Testando MDIC..."
if timeout 30 npx tsx scripts/collect.ts mdic-regional 2>&1 | grep -q "✅"; then
    echo "✅ MDIC funcionando"
else
    echo "❌ MDIC ainda com erro"
fi

echo "Testando FIESP..."
if timeout 30 npx tsx scripts/collect.ts fiesp-data 2>&1 | grep -q "✅"; then
    echo "✅ FIESP funcionando"
else
    echo "❌ FIESP ainda com erro"
fi

echo ""
echo "=============================================="
echo "✅ Correções Aplicadas!"
echo "=============================================="
echo ""
echo "Próximo passo:"
echo "  ./run-collectors-with-notifications.sh"
echo ""
