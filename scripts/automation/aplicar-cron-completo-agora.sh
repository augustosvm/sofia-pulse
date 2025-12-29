#!/bin/bash
################################################################################
# APLICAR CRONTAB COMPLETO - 55 Coletores + Vagas + Analytics + Email
################################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 APLICANDO CRONTAB COMPLETO"
echo "════════════════════════════════════════════════════════════════"

cd /home/ubuntu/sofia-pulse

# 1. Fazer backup
echo "📋 Fazendo backup do crontab atual..."
crontab -l > /tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt 2>/dev/null || true

# 2. Aplicar o crontab base (55 coletores + analytics + email)
echo "⚙️  Aplicando crontab base (55 coletores)..."
bash install-crontab-distributed-all.sh

# 3. Adicionar coletores de vagas
echo "💼 Adicionando coletores de vagas (3x por dia)..."
(crontab -l 2>/dev/null; cat << 'EOF'

# ============================================================================
# COLETORES DE VAGAS - 3x por dia
# ============================================================================

# 10:00 BRT (13:50 UTC) - Manhã
50 13 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-morning.log 2>&1

# 15:00 BRT (18:30 UTC) - Tarde
30 18 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-afternoon.log 2>&1

# 18:00 BRT (21:50 UTC) - Noite
50 21 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-evening.log 2>&1

EOF
) | crontab -

# 4. Verificar
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ CRONTAB APLICADO COM SUCESSO!"
echo "════════════════════════════════════════════════════════════════"
echo ""

TOTAL_JOBS=$(crontab -l | grep -c "cd.*SOFIA_DIR\|cd /home/ubuntu/sofia-pulse" || echo "0")
VAGAS=$(crontab -l | grep -c "run-jobs-collectors.sh" || echo "0")
ANALYTICS=$(crontab -l | grep -c "run-mega-analytics" || echo "0")
EMAIL=$(crontab -l | grep -c "send-email-mega" || echo "0")

echo "📊 RESUMO:"
echo "   • Total de jobs: $TOTAL_JOBS"
echo "   • Coletores de vagas: $VAGAS (esperado: 3)"
echo "   • Analytics: $ANALYTICS (esperado: 1)"
echo "   • Email: $EMAIL (esperado: 1)"
echo ""
echo "📅 PRÓXIMAS EXECUÇÕES DOS COLETORES DE VAGAS:"
crontab -l | grep "run-jobs-collectors.sh" | while read line; do
    HOUR=$(echo "$line" | awk '{print $2}')
    MIN=$(echo "$line" | awk '{print $1}')
    echo "   • ${HOUR}:${MIN} UTC"
done
echo ""
echo "📝 Ver crontab completo: crontab -l"
echo "📊 Monitorar logs: tail -f /var/log/sofia/*.log"
echo ""
