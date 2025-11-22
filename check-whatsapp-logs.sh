#!/bin/bash
echo "════════════════════════════════════════════════════════════════"
echo "🔍 VERIFICANDO LOGS DO SOFIA-MASTRA-RAG"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Try Docker first
if docker ps | grep -q sofia-mastra; then
    echo "📦 Detectado: sofia-mastra-rag em Docker"
    echo ""
    echo "Últimos logs relacionados a WhatsApp:"
    echo "─────────────────────────────────────────────────────────────"
    docker logs sofia-mastra-api --tail 200 | grep -i -E "whatsapp|unauthorized|forbidden|sent|failed|error" | tail -50
    echo "─────────────────────────────────────────────────────────────"
    
# Try PM2
elif pm2 list | grep -q sofia-mastra; then
    echo "⚙️  Detectado: sofia-mastra-rag em PM2"
    echo ""
    echo "Últimos logs relacionados a WhatsApp:"
    echo "─────────────────────────────────────────────────────────────"
    pm2 logs sofia-mastra-api --lines 200 --nostream | grep -i -E "whatsapp|unauthorized|forbidden|sent|failed|error" | tail -50
    echo "─────────────────────────────────────────────────────────────"
    
else
    echo "❌ sofia-mastra-rag não encontrado (nem Docker nem PM2)"
    echo ""
    echo "Onde está rodando o sofia-mastra-rag?"
    echo "  1. Em outro servidor? (precisa SSH)"
    echo "  2. Como systemd service?"
    echo "  3. Direto com npm/yarn?"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔎 PROCURE POR:"
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ 'WhatsApp message sent successfully'"
echo "  ❌ 'Unauthorized number'"
echo "  ❌ 'Number not registered'"
echo "  ❌ 'Insufficient credits'"
echo "  ❌ 'WhatsApp API error'"
echo ""
