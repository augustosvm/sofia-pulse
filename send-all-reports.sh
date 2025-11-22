#!/bin/bash
################################################################################
# SOFIA PULSE - SEND ALL REPORTS (EMAIL + WHATSAPP)
# Sends all 23 reports + CSVs via email AND summaries via WhatsApp
################################################################################

set -e

SOFIA_DIR="/home/user/sofia-pulse"
[ -d "/home/ubuntu/sofia-pulse" ] && SOFIA_DIR="/home/ubuntu/sofia-pulse"

cd "$SOFIA_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "📧📱 SOFIA PULSE - SEND ALL REPORTS"
echo "════════════════════════════════════════════════════════════════"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Will send:"
echo "  📧 Email: All 23 reports + CSVs"
echo "  📱 WhatsApp: Summaries of key reports"
echo ""

# ============================================================================
# STEP 1: SEND EMAIL (All 23 reports + CSVs)
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "📧 STEP 1: SENDING EMAIL"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash send-email-mega.sh

EMAIL_STATUS=$?

if [ $EMAIL_STATUS -eq 0 ]; then
    echo "✅ Email sent successfully"
else
    echo "❌ Email failed (status: $EMAIL_STATUS)"
fi

echo ""

# ============================================================================
# STEP 2: SEND WHATSAPP SUMMARIES
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "📱 STEP 2: SENDING WHATSAPP SUMMARIES"
echo "════════════════════════════════════════════════════════════════"
echo ""

python3 scripts/send-whatsapp-reports.py

WHATSAPP_STATUS=$?

if [ $WHATSAPP_STATUS -eq 0 ]; then
    echo "✅ WhatsApp summaries sent successfully"
else
    echo "⚠️  WhatsApp summaries failed (status: $WHATSAPP_STATUS)"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "📊 SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""

REPORTS_COUNT=$(ls analytics/*-latest.txt 2>/dev/null | wc -l)
CSV_COUNT=$(ls data/exports/*.csv 2>/dev/null | wc -l)

echo "Reports generated: $REPORTS_COUNT"
echo "CSVs exported: $CSV_COUNT"
echo ""

if [ $EMAIL_STATUS -eq 0 ]; then
    echo "✅ Email: Sent to augustosvm@gmail.com"
    echo "   Contains: All $REPORTS_COUNT reports + $CSV_COUNT CSVs"
else
    echo "❌ Email: Failed"
fi

echo ""

if [ $WHATSAPP_STATUS -eq 0 ]; then
    echo "✅ WhatsApp: Sent to +55 27 98802-4062"
    echo "   Contains: ~8-10 messages with key summaries"
else
    echo "⚠️  WhatsApp: Failed (sofia-mastra-rag running?)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Check your:"
echo "  📧 Email: augustosvm@gmail.com"
echo "  📱 WhatsApp: +55 27 98802-4062"
echo ""

if [ $EMAIL_STATUS -ne 0 ] || [ $WHATSAPP_STATUS -ne 0 ]; then
    echo "⚠️  Some deliveries failed. Check logs above."
    exit 1
fi

exit 0
