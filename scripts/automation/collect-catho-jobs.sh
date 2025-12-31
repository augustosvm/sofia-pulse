#!/bin/bash
# Collect Catho jobs with full parsing (salary, skills, seniority, remote, sector)
# Run daily to collect Brazilian tech jobs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_DIR"

echo "🇧🇷 [Catho] Collecting Brazilian tech jobs..."
echo "=========================================="

npx tsx scripts/collect-catho-final.ts

echo ""
echo "✅ [Catho] Collection complete!"
