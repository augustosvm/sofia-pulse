#!/bin/bash

################################################################################
# Sofia Pulse - Limited APIs Collection WITH WHATSAPP ALERTS
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env
set -a
source .env 2>/dev/null || true
set +a

# Track failures
FAILED_COLLECTORS=()
TOTAL_COLLECTORS=0

# Function to run collector with tracking
run_collector() {
    local name="$1"
    local cmd="$2"

    TOTAL_COLLECTORS=$((TOTAL_COLLECTORS + 1))
    echo ""
    echo "▶️  $name..."

    if eval "$cmd" 2>&1; then
        echo "✅ $name - Success"
    else
        echo "❌ $name - Failed"
        FAILED_COLLECTORS+=("$name")
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo "⚡ SOFIA PULSE - LIMITED APIs COLLECTION WITH ALERTS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

################################################################################
# GITHUB COLLECTORS
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "🐙 GITHUB COLLECTORS"
echo "════════════════════════════════════════════════════════════════"

run_collector "GitHub Trending" "npx tsx scripts/collect-github-trending.ts"
sleep 60

run_collector "GitHub Niches" "npx tsx scripts/collect-github-niches.ts"
sleep 60

################################################################################
# REDDIT COLLECTORS
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🤖 REDDIT COLLECTOR"
echo "════════════════════════════════════════════════════════════════"

run_collector "Reddit Tech" "npx tsx scripts/collect-reddit-tech.ts"
sleep 60

################################################################################
# RESEARCH COLLECTORS
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📚 RESEARCH COLLECTORS"
echo "════════════════════════════════════════════════════════════════"

run_collector "OpenAlex Papers" "npx tsx scripts/collect-openalex.ts"
sleep 60

run_collector "NIH Grants" "npx tsx scripts/collect-nih-grants.ts"
sleep 60

run_collector "Asia Universities" "npx tsx scripts/collect-asia-universities.ts"
sleep 60

################################################################################
# OTHER LIMITED APIs
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌍 OTHER LIMITED APIs"
echo "════════════════════════════════════════════════════════════════"

run_collector "GDELT Events" "npx tsx scripts/collect-gdelt.ts"
sleep 60

run_collector "AI Regulation" "npx tsx scripts/collect-ai-regulation.ts"
sleep 60

run_collector "EPO Patents" "npx tsx scripts/collect-epo-patents.ts"
sleep 60

run_collector "WIPO Patents" "npx tsx scripts/collect-wipo-china-patents.ts"

################################################################################
# SUMMARY & WHATSAPP ALERT
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ COLLECTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Total collectors: $TOTAL_COLLECTORS"
echo "❌ Failed: ${#FAILED_COLLECTORS[@]}"
echo ""

if [ ${#FAILED_COLLECTORS[@]} -gt 0 ]; then
    echo "Failed collectors:"
    for collector in "${FAILED_COLLECTORS[@]}"; do
        echo "  • $collector"
    done
fi

# Send WhatsApp summary
if command -v python3 &> /dev/null; then
    python3 -c "
import sys
import os
sys.path.insert(0, 'scripts/utils')

try:
    from whatsapp_notifier import WhatsAppNotifier
    whatsapp = WhatsAppNotifier()

    failed = [$(printf "'%s'," "${FAILED_COLLECTORS[@]}" | sed 's/,$//')]
    total = $TOTAL_COLLECTORS
    success = total - len(failed)

    status = '✅' if not failed else '⚠️'
    failures = '\\n'.join([f'• {c}' for c in failed]) if failed else 'None'

    message = f'''{status} Limited APIs Collection

📊 Total: {total}
✅ Success: {success}
❌ Failed: {len(failed)}

{failures}'''

    whatsapp.send(message)
    print('📱 WhatsApp summary sent')
except Exception as e:
    print(f'⚠️  WhatsApp notification failed: {e}')
"
fi

echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
