#!/bin/bash
################################################################################
# RESTAURAR CRONTAB COMPLETO - Sofia Pulse
# Aplica o crontab distribuído com todos os 55 coletores
################################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🔧 RESTAURANDO CRONTAB COMPLETO - SOFIA PULSE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Verificar se estamos no servidor
if [[ "$PWD" == /mnt/c/* ]]; then
    echo "⚠️  ERRO: Você está no Windows/WSL!"
    echo "   Execute este script no servidor:"
    echo "   ssh ubuntu@91.98.158.19"
    echo "   cd /home/ubuntu/sofia-pulse"
    echo "   bash restore-crontab-now.sh"
    exit 1
fi

# Backup do crontab atual
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"
echo "📋 Backup salvo: $BACKUP_FILE"
echo ""

# Verificar se o script install-crontab-distributed-all.sh existe
if [ ! -f "install-crontab-distributed-all.sh" ]; then
    echo "❌ ERRO: Arquivo install-crontab-distributed-all.sh não encontrado!"
    echo "   Certifique-se de estar no diretório /home/ubuntu/sofia-pulse"
    exit 1
fi

# Aplicar crontab distribuído
echo "🚀 Aplicando crontab distribuído completo..."
bash install-crontab-distributed-all.sh

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ CRONTAB RESTAURADO COM SUCESSO!"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Verificar instalação
COLLECTOR_COUNT=$(crontab -l 2>/dev/null | grep -c 'collect-' || echo "0")
echo "📊 Coletores instalados: $COLLECTOR_COUNT/55"
echo ""

# Mostrar jobs para 18:00 UTC (15:00 BRT)
echo "📅 Jobs programados para 18:00 UTC (15:00 BRT):"
crontab -l 2>/dev/null | grep "^0 18\|^20 18" || echo "   Nenhum encontrado"
echo ""

# Verificar serviço cron
if systemctl is-active --quiet cron; then
    echo "✅ Serviço cron está ATIVO"
else
    echo "⚠️  Serviço cron está INATIVO - iniciando..."
    sudo systemctl start cron
fi

echo ""
echo "📝 Próximos passos:"
echo "   1. Verificar logs: tail -f /var/log/sofia/brazil-security.log"
echo "   2. Testar manualmente: cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/collect-brazil-security.py"
echo "   3. Aguardar próxima execução às 18:00 UTC (15:00 BRT)"
echo ""
