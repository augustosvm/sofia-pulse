#!/bin/bash
################################################################################
# SOFIA PULSE - RUN ALL COLLECTORS WITH FULL MONITORING
# Executes all collections with healthchecks and sanity validation
################################################################################

set -e

SOFIA_DIR="/home/user/sofia-pulse"
[ -d "/home/ubuntu/sofia-pulse" ] && SOFIA_DIR="/home/ubuntu/sofia-pulse"

cd "$SOFIA_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - COMPLETE DATA COLLECTION WITH MONITORING"
echo "════════════════════════════════════════════════════════════════"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Ensure monitoring is setup
if [ ! -d "/var/log/sofia/collectors" ]; then
    echo "⚠️  Monitoring not setup. Running setup..."
    bash setup-monitoring.sh
fi

# ============================================================================
# STEP 1: PRE-FLIGHT HEALTHCHECK
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "🏥 STEP 1: PRE-FLIGHT HEALTHCHECK"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash healthcheck-collectors.sh || echo "⚠️  Some collectors unhealthy (will retry)"
echo ""

# ============================================================================
# STEP 2: RUN FAST APIs (No Rate Limits)
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "⚡ STEP 2: FAST APIs (No Rate Limits)"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash collect-fast-apis.sh || echo "⚠️  Some fast APIs failed"
echo ""

# ============================================================================
# STEP 3: RUN LIMITED APIs (With Rate Limiting)
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "🐌 STEP 3: LIMITED APIs (Rate Limited)"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash collect-limited-apis.sh || echo "⚠️  Some limited APIs failed"
echo ""

# ============================================================================
# STEP 4: DATA SANITY CHECK
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "🔍 STEP 4: DATA SANITY CHECK"
echo "════════════════════════════════════════════════════════════════"
echo ""

python3 scripts/sanity-check.py || echo "⚠️  Some sanity checks failed"
echo ""

# ============================================================================
# STEP 5: RUN ANALYTICS (All 23 Reports)
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "📊 STEP 5: ANALYTICS (23 Reports)"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash run-mega-analytics.sh || echo "⚠️  Some analytics failed"
echo ""

# ============================================================================
# STEP 6: POST-RUN HEALTHCHECK
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "🏥 STEP 6: POST-RUN HEALTHCHECK"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash healthcheck-collectors.sh || echo "⚠️  Some collectors still unhealthy"
echo ""

# ============================================================================
# STEP 7: SEND EMAIL REPORT
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "📧 STEP 7: SEND EMAIL REPORT"
echo "════════════════════════════════════════════════════════════════"
echo ""

bash send-email-mega.sh || echo "⚠️  Email sending failed"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "✅ COMPLETE PIPELINE FINISHED"
echo "════════════════════════════════════════════════════════════════"
echo "Completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "📊 Check results:"
echo "  • Logs: /var/log/sofia/collectors/"
echo "  • Reports: analytics/*-latest.txt"
echo "  • CSVs: data/exports/*.csv"
echo ""
echo "🏥 Health status:"
bash healthcheck-collectors.sh 2>&1 | tail -10
echo ""
echo "════════════════════════════════════════════════════════════════"
