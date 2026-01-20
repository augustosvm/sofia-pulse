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

# Reset counts to avoid variable leakage from previous runs if source-d
INSERTS=""

# Extract insert count from output (try multiple patterns)
# Pattern 1: "Collected: 123" or "Total collected: 123"
INSERTS=$(echo "$OUTPUT" | grep -oP "(Total\s+)?[Cc]ollected:\s*\K\d+" | tail -1)

# Pattern 2: "Inserted 123" or "✅ Inserted 123"
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "Inserted\s*\K\d+" | tail -1)
fi

# Pattern 3: "Inseridas: 123" (Portuguese - InfoJobs)
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "Inseridas:\s*\K\d+" | tail -1)
fi

# Pattern 4: "✅ Saved 123" or "Saved 123"
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "Saved\s*\K\d+" | tail -1)
fi

# Pattern 5: "✅ 123" at end of output (common pattern)
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "✅\s*\K\d+" | tail -1)
fi

# Pattern 6: Generic number before "records", "vagas", "jobs", "items"
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "\d+(?=\s+(records|vagas|jobs|items|entries|papers|companies|organizations))" | tail -1)
fi

# Pattern 7: "Salvos: 123" or "Novos: 123" (Portuguese)
if [ -z "$INSERTS" ]; then
    INSERTS=$(echo "$OUTPUT" | grep -oP "(Salvos|Novos):\s*\K\d+" | tail -1)
fi

# Fallback
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
