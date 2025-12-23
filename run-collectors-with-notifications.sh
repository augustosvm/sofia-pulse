#!/bin/bash
# Sofia Pulse Collector Runner with WhatsApp Notifications
# Runs all collectors, tracks INSERT counts, and sends WhatsApp updates

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

LOG_FILE="logs/collectors-$(date +%Y%m%d-%H%M%S).log"
TEMP_OUTPUT="/tmp/sofia-collector-output-$$.txt"

echo "🚀 Starting collectors at $(date)" | tee -a "$LOG_FILE"

# Fast collectors (run every hour)
COLLECTORS=(
    "github"
    "hackernews"
    "stackoverflow"
    "himalayas"
    "remoteok"
    "ai-companies"
    "universities"
    "ngos"
    "yc-companies"
    "nvd"
    "cisa"
    "gdelt"
    "mdic-regional"
    "fiesp-data"
)

SUCCESS=0
FAILED=0
TOTAL_INSERTS=0

# Function to send WhatsApp notification
send_whatsapp() {
    local message="$1"
    python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/scripts/utils')
from sofia_whatsapp_integration import SofiaWhatsAppIntegration
integration = SofiaWhatsAppIntegration()
integration.send_whatsapp_direct('''$message''')
"
}

# Send start notification
START_TIME=$(date +%s)
send_whatsapp "🚀 *Sofia Pulse - Iniciando Coleta*

📅 $(date '+%d/%m/%Y %H:%M')
📊 ${#COLLECTORS[@]} collectors agendados

_Aguarde notificações individuais..._"

for collector in "${COLLECTORS[@]}"; do
    CURRENT=$((SUCCESS+FAILED+1))
    echo "[$CURRENT/${#COLLECTORS[@]}] Running: $collector" | tee -a "$LOG_FILE"
    
    # Run collector and capture output
    if timeout 300 npx tsx scripts/collect.ts "$collector" > "$TEMP_OUTPUT" 2>&1; then
        # Extract insert count from output
        INSERTS=$(grep -oP '✅ Inserted \K\d+' "$TEMP_OUTPUT" | head -1)
        if [ -z "$INSERTS" ]; then
            # Try alternative patterns
            INSERTS=$(grep -oP 'Inserted: \K\d+' "$TEMP_OUTPUT" | head -1)
        fi
        if [ -z "$INSERTS" ]; then
            INSERTS="?"
        fi
        
        # Get any error/warning messages
        WARNINGS=$(grep -i "warn\|error" "$TEMP_OUTPUT" | head -3 | sed 's/^/  /')
        
        echo "  ✅ Success - Inserted: $INSERTS records" | tee -a "$LOG_FILE"
        cat "$TEMP_OUTPUT" >> "$LOG_FILE"
        
        ((SUCCESS++))
        if [ "$INSERTS" != "?" ]; then
            TOTAL_INSERTS=$((TOTAL_INSERTS + INSERTS))
        fi
        
        # Send individual success notification
        if [ "$INSERTS" != "?" ]; then
            send_whatsapp "✅ *$collector*
📊 $INSERTS novos registros
⏱️ [$CURRENT/${#COLLECTORS[@]}]"
        else
            send_whatsapp "✅ *$collector*
✓ Executado com sucesso
⏱️ [$CURRENT/${#COLLECTORS[@]}]"
        fi
    else
        # Extract error from output
        ERROR=$(tail -5 "$TEMP_OUTPUT" | grep -i "error" | head -1)
        if [ -z "$ERROR" ]; then
            ERROR="Timeout ou erro desconhecido"
        fi
        
        echo "  ❌ Failed - $ERROR" | tee -a "$LOG_FILE"
        cat "$TEMP_OUTPUT" >> "$LOG_FILE"
        
        ((FAILED++))
        
        # Send individual failure notification
        send_whatsapp "❌ *$collector*
⚠️ Falhou
📝 ${ERROR:0:100}
⏱️ [$CURRENT/${#COLLECTORS[@]}]"
    fi
    
    # Small delay between collectors
    sleep 2
done

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo "" | tee -a "$LOG_FILE"
echo "✅ Completed: $SUCCESS/${#COLLECTORS[@]}" | tee -a "$LOG_FILE"
echo "❌ Failed: $FAILED/${#COLLECTORS[@]}" | tee -a "$LOG_FILE"
echo "📊 Total Inserts: $TOTAL_INSERTS" | tee -a "$LOG_FILE"
echo "⏱️  Duration: ${MINUTES}m ${SECONDS}s" | tee -a "$LOG_FILE"
echo "Finished at $(date)" | tee -a "$LOG_FILE"

# Send final summary
SUCCESS_RATE=$((SUCCESS * 100 / ${#COLLECTORS[@]}))
send_whatsapp "🏁 *Sofia Pulse - Coleta Finalizada*

✅ Sucesso: $SUCCESS/${#COLLECTORS[@]} ($SUCCESS_RATE%)
❌ Falhas: $FAILED/${#COLLECTORS[@]}
📊 *Total Inserido: $TOTAL_INSERTS registros*
⏱️  Duração: ${MINUTES}m ${SECONDS}s

📅 $(date '+%d/%m/%Y %H:%M')

_Próxima execução em 1 hora_"

# Keep only last 7 days of logs
find logs -name "collectors-*.log" -mtime +7 -delete

# Cleanup
rm -f "$TEMP_OUTPUT"
