#!/bin/bash
# Wrapper to run collector and send WhatsApp notification (BEST-EFFORT)
# Usage: ./collect-with-notification.sh <collector-name>

COLLECTOR_NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -z "$COLLECTOR_NAME" ]; then
    echo "Usage: $0 <collector-name>"
    exit 1
fi

# Run collector and capture output
OUTPUT=$(npx tsx scripts/collect.ts "$COLLECTOR_NAME" 2>&1)
COLLECTOR_EXIT_CODE=$?

# Extract insert count from output (try multiple patterns)
INSERTS=$(echo "$OUTPUT" | grep -oP "(Total\s+)?[Cc]ollected:\s*\K\d+" | tail -1)
if [ -z "$INSERTS" ]; then INSERTS=$(echo "$OUTPUT" | grep -oP "Inserted\s*\K\d+" | tail -1); fi
if [ -z "$INSERTS" ]; then INSERTS=$(echo "$OUTPUT" | grep -oP "Inseridas:\s*\K\d+" | tail -1); fi
if [ -z "$INSERTS" ]; then INSERTS=$(echo "$OUTPUT" | grep -oP "Saved\s*\K\d+" | tail -1); fi
if [ -z "$INSERTS" ]; then INSERTS=$(echo "$OUTPUT" | grep -oP "✅\s*\K\d+" | tail -1); fi
if [ -z "$INSERTS" ]; then INSERTS=$(echo "$OUTPUT" | grep -oP "\d+(?=\s+(records|vagas|jobs|items|entries|papers|companies|organizations))" | tail -1); fi
if [ -z "$INSERTS" ]; then INSERTS=$(echo "$OUTPUT" | grep -oP "(Salvos|Novos):\s*\K\d+" | tail -1); fi
if [ -z "$INSERTS" ]; then INSERTS="?"; fi

# Build message
if [ $COLLECTOR_EXIT_CODE -eq 0 ]; then
    MESSAGE="✅ $COLLECTOR_NAME\n📊 $INSERTS novos registros"
else
    ERROR=$(echo "$OUTPUT" | grep -i "error" | head -1 | cut -c1-100)
    MESSAGE="❌ $COLLECTOR_NAME\n⚠️ Erro: ${ERROR:-Falha desconhecida}"
fi

# Send WhatsApp notification (BEST-EFFORT - does not affect exit code)
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/utils')
try:
    from sofia_whatsapp_integration import SofiaWhatsAppIntegration
    integration = SofiaWhatsAppIntegration()
    integration.send_whatsapp_direct('''$MESSAGE''')
except Exception as e:
    print(f'[WhatsApp] Warning: notification failed - {type(e).__name__}: {str(e)[:100]}', file=sys.stderr)
" 2>&1 | grep -E '\[WhatsApp\]' || true

# CRITICAL: Return collector exit code, NOT WhatsApp exit code
exit $COLLECTOR_EXIT_CODE
