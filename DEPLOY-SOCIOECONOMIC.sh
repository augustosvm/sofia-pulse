#!/bin/bash
# ============================================================================
# SOFIA PULSE - DEPLOY SOCIOECONOMIC INDICATORS v2.0
# ============================================================================
# Última atualização: 2025-11-19
# Indicadores: 56 (42 originais + 14 novos)
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "🚀 SOFIA PULSE - DEPLOY SOCIOECONOMIC INDICATORS v2.0"
echo "============================================================================"
echo ""

# ============================================================================
# STEP 0: Git Pull
# ============================================================================

echo "📥 STEP 0: Pulling latest code..."
cd /home/ubuntu/sofia-pulse

git pull origin claude/fix-sql-syntax-error-015w5Ss8ZiqFEJziiWrN7Rs1

echo "✅ Code updated"
echo ""

# ============================================================================
# STEP 1: Verify Files
# ============================================================================

echo "🔍 STEP 1: Verifying files..."

if [ ! -f "scripts/collect-socioeconomic-indicators.py" ]; then
    echo "❌ ERROR: collect-socioeconomic-indicators.py not found"
    exit 1
fi

echo "✅ Collector script found"

# Count indicators in file
INDICATOR_COUNT=$(grep -c "^    '[A-Z]" scripts/collect-socioeconomic-indicators.py || echo "0")
echo "   Found $INDICATOR_COUNT indicators in script"

if [ "$INDICATOR_COUNT" -ne 56 ]; then
    echo "⚠️  WARNING: Expected 56 indicators, found $INDICATOR_COUNT"
fi

echo ""

# ============================================================================
# STEP 2: Setup Python Virtual Environment
# ============================================================================

echo "🐍 STEP 2: Setting up Python environment..."

if [ ! -d "venv-analytics" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv-analytics
fi

source venv-analytics/bin/activate

echo "   Installing dependencies..."
pip install -q requests psycopg2-binary python-dotenv

echo "✅ Python environment ready"
echo ""

# ============================================================================
# STEP 3: Verify Database Connection
# ============================================================================

echo "🗄️  STEP 3: Verifying database..."

# Check if table exists
TABLE_EXISTS=$(psql -U sofia -d sofia_db -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='sofia' AND table_name='socioeconomic_indicators');" 2>/dev/null || echo "f")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo "✅ Table socioeconomic_indicators exists"

    # Count existing records
    CURRENT_COUNT=$(psql -U sofia -d sofia_db -tAc "SELECT COUNT(*) FROM sofia.socioeconomic_indicators;" 2>/dev/null || echo "0")
    echo "   Current records: $CURRENT_COUNT"
else
    echo "⚠️  Table does not exist - will be created on first run"
fi

echo ""

# ============================================================================
# STEP 4: Test Collector (Dry Run)
# ============================================================================

echo "🧪 STEP 4: Testing collector (syntax check)..."

python3 -m py_compile scripts/collect-socioeconomic-indicators.py

if [ $? -eq 0 ]; then
    echo "✅ Python syntax OK"
else
    echo "❌ ERROR: Python syntax error"
    exit 1
fi

echo ""

# ============================================================================
# STEP 5: Run Collector
# ============================================================================

echo "🌍 STEP 5: Running socioeconomic collector..."
echo "   This will fetch ~95,000 records from World Bank API"
echo "   Estimated time: 3-5 minutes"
echo ""

python3 scripts/collect-socioeconomic-indicators.py

echo ""
echo "✅ Collector finished"
echo ""

# ============================================================================
# STEP 6: Verify Results
# ============================================================================

echo "✅ STEP 6: Verifying results..."

FINAL_COUNT=$(psql -U sofia -d sofia_db -tAc "SELECT COUNT(*) FROM sofia.socioeconomic_indicators;" 2>/dev/null || echo "0")
INDICATOR_COUNT_DB=$(psql -U sofia -d sofia_db -tAc "SELECT COUNT(DISTINCT indicator_code) FROM sofia.socioeconomic_indicators;" 2>/dev/null || echo "0")
COUNTRY_COUNT=$(psql -U sofia -d sofia_db -tAc "SELECT COUNT(DISTINCT country_code) FROM sofia.socioeconomic_indicators;" 2>/dev/null || echo "0")

echo "   Total records: $FINAL_COUNT"
echo "   Unique indicators: $INDICATOR_COUNT_DB"
echo "   Countries: $COUNTRY_COUNT"

if [ "$FINAL_COUNT" -gt 50000 ]; then
    echo "✅ SUCCESS: Data collection complete"
else
    echo "⚠️  WARNING: Expected >50,000 records, got $FINAL_COUNT"
fi

echo ""

# ============================================================================
# STEP 7: Update Crontab
# ============================================================================

echo "⏰ STEP 7: Updating crontab..."

# Check if cron entry exists
CRON_EXISTS=$(crontab -l 2>/dev/null | grep -c "run-all-with-venv.sh" || echo "0")

if [ "$CRON_EXISTS" -eq 0 ]; then
    echo "   Adding crontab entry..."
    (crontab -l 2>/dev/null; echo "0 13 * * * cd /home/ubuntu/sofia-pulse && bash run-all-with-venv.sh >> /tmp/sofia-python.log 2>&1") | crontab -
    echo "✅ Crontab entry added (runs daily at 13:00 UTC = 10:00 BRT)"
else
    echo "✅ Crontab entry already exists"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "============================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "============================================================================"
echo ""
echo "📊 System Status:"
echo "   • Indicators: 56 (6 economy, 2 poverty, 4 demographics, 17 health, 7 education, 6 environment, 3 tech, 1 innovation, 4 infrastructure)"
echo "   • Records in DB: $FINAL_COUNT"
echo "   • Countries: $COUNTRY_COUNT"
echo "   • Data period: 2015-2024"
echo "   • Source: World Bank API (free)"
echo ""
echo "⏰ Automation:"
echo "   • Runs daily at 13:00 UTC (10:00 BRT)"
echo "   • Logs: /tmp/sofia-python.log"
echo ""
echo "📈 Next Steps:"
echo "   1. Run queries from PACKAGE-COMPLETE-SOCIOECONOMIC.md"
echo "   2. Monitor /tmp/sofia-python.log for daily runs"
echo "   3. Check analytics reports for socioeconomic insights"
echo ""
echo "🎯 Quick Test Query:"
echo "   psql -U sofia -d sofia_db -c \"SELECT country_name, value FROM sofia.socioeconomic_indicators WHERE indicator_code='NY.GDP.PCAP.CD' AND year=2023 ORDER BY value DESC LIMIT 10;\""
echo ""
echo "============================================================================"
echo "🚀 System ready for production!"
echo "============================================================================"
