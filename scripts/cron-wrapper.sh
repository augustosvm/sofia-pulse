#!/bin/bash
################################################################################
# Cron Wrapper - Executa coletor e envia notificação WhatsApp
# Uso: cron-wrapper.sh <script> <nome>
################################################################################

SCRIPT=$1
NAME=$2
SOFIA_DIR=/home/ubuntu/sofia-pulse

cd $SOFIA_DIR

# Carregar variáveis de ambiente
set -a
source .env 2>/dev/null || true
set +a

# Executar o script
if [[ $SCRIPT == *.ts ]]; then
    OUTPUT=$(npx tsx scripts/$SCRIPT 2>&1)
    EXIT_CODE=$?
elif [[ $SCRIPT == *.py ]]; then
    source venv-analytics/bin/activate
    OUTPUT=$(python3 scripts/$SCRIPT 2>&1)
    EXIT_CODE=$?
else
    OUTPUT=$(bash scripts/$SCRIPT 2>&1)
    EXIT_CODE=$?
fi

# Extrair número de registros coletados
COLLECTED=$(echo "$OUTPUT" | grep -oP "Collected:? \K\d+" | head -1)
if [ -z "$COLLECTED" ]; then
    COLLECTED=$(echo "$OUTPUT" | grep -oP "\d+ (new )?jobs?" | head -1 | grep -oP "\d+")
fi
if [ -z "$COLLECTED" ]; then
    COLLECTED=$(echo "$OUTPUT" | grep -oP "\d+ registros?" | head -1 | grep -oP "\d+")
fi

# Enviar WhatsApp
if [ $EXIT_CODE -eq 0 ]; then
    if [ -n "$COLLECTED" ] && [ "$COLLECTED" -gt 0 ]; then
        MSG="✅ $NAME
📊 Coletados: $COLLECTED registros
⏰ $(date '+%H:%M')"
    else
        MSG="✅ $NAME
✓ Executado com sucesso
⏰ $(date '+%H:%M')"
    fi
else
    MSG="❌ $NAME
⚠️ Erro na execução
⏰ $(date '+%H:%M')"
fi

# Enviar via WhatsApp
python3 -c "
from scripts.utils.whatsapp_alerts import send_whatsapp_info
send_whatsapp_info('$MSG')
" 2>/dev/null || echo "WhatsApp notification skipped"

exit $EXIT_CODE
