#!/bin/bash
# Wrapper to run a single collector with WhatsApp notification

COLLECTOR=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Add random delay (0-10 seconds) to prevent spam detection
DELAY=$((RANDOM % 11))
sleep $DELAY

# Run collector and capture output
OUTPUT=$(npx tsx scripts/collect.ts "$COLLECTOR" 2>&1)
EXIT_CODE=$?

# Extract stats from output
INSERTS=$(echo "$OUTPUT" | grep -oP 'Inserted \K[0-9]+' | tail -1)
ERRORS=$(echo "$OUTPUT" | grep -oP 'Errors: \K[0-9]+' | tail -1)

# Determine status and message
if [ $EXIT_CODE -eq 0 ] && [ "$ERRORS" == "0" ]; then
    STATUS="✅"
    MSG="$STATUS $COLLECTOR\n✓ Executado com sucesso\n📊 ${INSERTS:-?} registros"
else
    STATUS="❌"
    MSG="$STATUS $COLLECTOR FALHOU\n❌ ${ERRORS:-?} erros"
fi

# Load WHATSAPP_NUMBER from .env
source "$SCRIPT_DIR/.env"

# Send WhatsApp notification with 5s delay
sleep 5

curl -X POST http://91.98.158.19:3001/send \
  -H 'Content-Type: application/json' \
  -d "{\"to\": \"$WHATSAPP_NUMBER\", \"message\": \"$MSG\"}" \
  -s > /dev/null

# Output to log
echo "$OUTPUT"
