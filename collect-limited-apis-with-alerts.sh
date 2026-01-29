#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Run the actual collection script
bash scripts/collect-limited-apis.sh

# Send WhatsApp alert (if available)
if [ -f "scripts/utils/whatsapp_notifier.py" ]; then
    python3 scripts/utils/whatsapp_notifier.py "Limited APIs collected successfully (ArXiv)" 2>/dev/null || true
fi

echo "✅ Limited APIs collection with alerts complete"
