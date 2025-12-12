#!/bin/bash
################################################################################
# APLICAÇÃO ESTRATÉGICA DO CRONTAB - Sofia Pulse
# Aplica o crontab de forma segura e verificada
################################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🎯 APLICAÇÃO ESTRATÉGICA DO CRONTAB"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. BACKUP do crontab atual
echo "📋 1. Fazendo backup do crontab atual..."
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# Sem crontab anterior" > "$BACKUP_FILE"
echo "   ✅ Backup salvo em: $BACKUP_FILE"
echo ""

# 2. VERIFICAR se os scripts existem
echo "🔍 2. Verificando scripts essenciais..."
MISSING=0

if [ ! -f "/home/ubuntu/sofia-pulse/run-jobs-collectors.sh" ]; then
    echo "   ❌ FALTA: run-jobs-collectors.sh"
    MISSING=1
fi

if [ ! -f "/home/ubuntu/sofia-pulse/run-mega-analytics-with-alerts.sh" ]; then
    echo "   ❌ FALTA: run-mega-analytics-with-alerts.sh"
    MISSING=1
fi

if [ ! -f "/home/ubuntu/sofia-pulse/send-email-mega.sh" ]; then
    echo "   ❌ FALTA: send-email-mega.sh"
    MISSING=1
fi

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  ATENÇÃO: Scripts essenciais estão faltando!"
    echo "   Continuando mesmo assim..."
fi
echo "   ✅ Verificação concluída"
echo ""

# 3. CRIAR diretório de logs
echo "📁 3. Criando diretório de logs..."
mkdir -p /var/log/sofia
chmod 755 /var/log/sofia
echo "   ✅ Diretório criado: /var/log/sofia"
echo ""

# 4. APLICAR o novo crontab
echo "⚙️  4. Aplicando novo crontab..."
if [ -f "/home/ubuntu/sofia-pulse/CRONTAB-FINAL-SIMPLES.txt" ]; then
    crontab /home/ubuntu/sofia-pulse/CRONTAB-FINAL-SIMPLES.txt
    echo "   ✅ Crontab aplicado com sucesso!"
else
    echo "   ❌ ERRO: Arquivo CRONTAB-FINAL-SIMPLES.txt não encontrado!"
    exit 1
fi
echo ""

# 5. VERIFICAR instalação
echo "✅ 5. Verificando instalação..."
TOTAL_JOBS=$(crontab -l | grep -c "cd \$SOFIA_DIR" || echo "0")
JOB_COLLECTORS=$(crontab -l | grep -c "run-jobs-collectors.sh" || echo "0")
ANALYTICS=$(crontab -l | grep -c "run-mega-analytics" || echo "0")

echo "   📊 Total de jobs no cron: $TOTAL_JOBS"
echo "   💼 Coletores de vagas: $JOB_COLLECTORS (esperado: 3)"
echo "   📈 Analytics: $ANALYTICS (esperado: 1)"
echo ""

# 6. VERIFICAR próxima execução
echo "⏰ 6. Próximas execuções dos coletores de vagas:"
echo ""
crontab -l | grep "run-jobs-collectors.sh" | while read line; do
    HOUR=$(echo "$line" | awk '{print $2}')
    MIN=$(echo "$line" | awk '{print $1}')
    echo "   • ${HOUR}:${MIN} UTC"
done
echo ""

# 7. TESTAR um coletor manualmente (opcional)
echo "🧪 7. Teste manual disponível:"
echo "   Para testar agora: cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh"
echo ""

# 8. RESUMO FINAL
echo "════════════════════════════════════════════════════════════════"
echo "✅ CRONTAB APLICADO COM SUCESSO!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📅 CRONOGRAMA DOS COLETORES DE VAGAS:"
echo "   • 10:00 BRT (13:00 UTC) - Manhã"
echo "   • 15:00 BRT (18:00 UTC) - Tarde"  
echo "   • 18:00 BRT (21:00 UTC) - Noite"
echo ""
echo "📊 ANALYTICS:"
echo "   • 19:00 BRT (22:00 UTC) - Mega Analytics"
echo "   • 19:30 BRT (22:30 UTC) - Email Report"
echo ""
echo "📝 MONITORAMENTO:"
echo "   • Logs: /var/log/sofia/*.log"
echo "   • Ver cron: crontab -l"
echo "   • Ver logs: tail -f /var/log/sofia/jobs-*.log"
echo ""
echo "💾 BACKUP SALVO EM: $BACKUP_FILE"
echo ""
echo "🎯 PRÓXIMA EXECUÇÃO: Verifique os horários acima"
echo ""
