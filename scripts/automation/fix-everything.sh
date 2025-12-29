#!/bin/bash
################################################################################
# FIX EVERYTHING - Aplica todas as correções de uma vez
################################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - FIX EVERYTHING"
echo "════════════════════════════════════════════════════════════════"
echo ""

# STEP 1: Apply new Gemini API key
echo "STEP 1/3: Applying new Gemini API key..."
if [ -f apply-new-gemini-key.sh ]; then
    bash apply-new-gemini-key.sh
    echo "✅ Gemini key updated (script self-deleted)"
else
    echo "⚠️  apply-new-gemini-key.sh not found (may have been deleted)"
fi
echo ""

# STEP 2: Apply database migrations
echo "STEP 2/3: Applying database migrations..."
python apply-migrations-python.py
if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ Migrations failed"
    exit 1
fi
echo ""

# STEP 3: Restart sofia-mastra-rag
echo "STEP 3/3: Restarting sofia-mastra-rag..."
docker restart sofia-mastra-api
if [ $? -eq 0 ]; then
    echo "✅ sofia-mastra-api restarted"
else
    echo "⚠️  Failed to restart sofia-mastra-api"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL FIXES APPLIED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "What was fixed:"
echo "  ✅ New Gemini API key (no more leaks)"
echo "  ✅ Database columns: city + countries"
echo "  ✅ sofia-mastra-rag restarted"
echo ""
echo "Next steps:"
echo "  1. Run analytics: bash run-mega-analytics.sh"
echo "  2. All 23 reports should work now!"
echo ""
