#!/bin/bash
# Wrapper to run collector and send WhatsApp notification
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
EXIT_CODE=$?

# Extract insert count from output
INSERTS=$(echo "$OUTPUT" | grep -oP "Collected:\s*\K\d+" | tail -1)
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "Inserted\s*\K\d+" | tail -1)
fi
if [ -z "$INSERTS" ]; then
    INSERTS="?"
fi

# Send WhatsApp notification
if [ $EXIT_CODE -eq 0 ]; then
    MESSAGE="✅ $COLLECTOR_NAME
📊 $INSERTS novos registros"
else
    ERROR=$(echo "$OUTPUT" | grep -i "error" | head -1 | cut -c1-100)
    MESSAGE="❌ $COLLECTOR_NAME
⚠️ Erro: ${ERROR:-Falha desconhecida}"
fi

# Send via Python
python3 << EOF
import sys
sys.path.append('$SCRIPT_DIR/utils')
from sofia_whatsapp_integration import SofiaWhatsAppIntegration
integration = SofiaWhatsAppIntegration()
integration.send_whatsapp_direct('''$MESSAGE''')
EOF

exit $EXIT_CODE
