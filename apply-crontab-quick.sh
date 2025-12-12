#!/bin/bash
# COPIE E COLE ESTE SCRIPT COMPLETO NO SERVIDOR
# Execute: bash apply-crontab-quick.sh

cd /home/ubuntu/sofia-pulse

echo "🔧 Aplicando crontab distribuído completo..."

# Fazer stash se necessário
git stash 2>/dev/null || true

# Aplicar crontab
bash install-crontab-distributed-all.sh

echo ""
echo "✅ Verificando instalação..."
COLLECTOR_COUNT=$(crontab -l 2>/dev/null | grep -c 'collect-' || echo "0")
echo "📊 Coletores instalados: $COLLECTOR_COUNT/55"

echo ""
echo "📅 Jobs das 15h BRT (18:00 UTC):"
crontab -l 2>/dev/null | grep "^0 18\|^20 18" || echo "Nenhum encontrado"

echo ""
echo "✅ CONCLUÍDO!"
