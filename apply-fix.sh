#!/bin/bash
#
# Sofia Pulse - Apply Fix
# Aplica correções para restaurar execução automática
#

set -e

echo "=================================================="
echo "SOFIA PULSE - APLICANDO CORREÇÕES"
echo "=================================================="
echo ""

# 1. Criar diretório de logs
echo "[1/6] Criando diretório de logs..."
sudo mkdir -p /var/log/sofia
sudo chown $USER:$USER /var/log/sofia
echo "  ✅ /var/log/sofia criado"
echo ""

# 2. Tornar wrapper executável
echo "[2/6] Configurando cron-wrapper.sh..."
chmod +x cron-wrapper.sh
echo "  ✅ cron-wrapper.sh executável"
echo ""

# 3. Testar sync_expected_set
echo "[3/6] Testando sync_expected_set.py..."
./cron-wrapper.sh python3 scripts/sync_expected_set.py
echo "  ✅ sync_expected_set.py OK"
echo ""

# 4. Backup crontab atual
echo "[4/6] Fazendo backup do crontab atual..."
crontab -l > crontab-backup-$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "Nenhum crontab anterior"
echo "  ✅ Backup criado"
echo ""

# 5. Instalar novo crontab
echo "[5/6] Instalando novo crontab..."
crontab crontab-corrected.txt
echo "  ✅ Crontab instalado"
echo ""

# 6. Verificar instalação
echo "[6/6] Verificando instalação..."
echo ""
echo "Crontab ativo:"
crontab -l | grep -E "(sync_expected|daily_pipeline|run_and_verify)"
echo ""

echo "=================================================="
echo "✅ CORREÇÕES APLICADAS COM SUCESSO"
echo "=================================================="
echo ""
echo "Próximos passos:"
echo "  1. Aguardar próxima execução do cron (23:40 BRT)"
echo "  2. Monitorar logs: tail -f /var/log/sofia/*.log"
echo "  3. Validar runs no banco: últimas 24h"
echo ""
echo "Execução manual de teste:"
echo "  ./cron-wrapper.sh python3 scripts/run_and_verify.py"
echo ""
