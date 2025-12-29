#!/bin/bash
# ============================================================================
# AI Technology Radar - Quick Test Script
# ============================================================================
# Tests a subset of collectors to verify setup
#
# Usage:
#   bash test-ai-tech-radar.sh
# ============================================================================

set -e

echo "================================================================================"
echo "🧪 AI TECH RADAR - QUICK TEST"
echo "================================================================================"

# Test database connection
echo ""
echo "1️⃣  Testing database connection..."
if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo "Please check your .env file and database credentials"
    exit 1
fi

# Run migration
echo ""
echo "2️⃣  Running database migration..."
if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -f db/migrations/020_create_ai_tech_radar.sql > /dev/null 2>&1; then
    echo "✅ Migration successful"
else
    echo "⚠️  Migration completed (tables may already exist)"
fi

# Create views
echo ""
echo "3️⃣  Creating SQL views..."
if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -f sql/04-ai-tech-radar-views.sql > /dev/null 2>&1; then
    echo "✅ Views created"
else
    echo "⚠️  Views creation completed (views may already exist)"
fi

# Test one collector (PyPI - fastest)
echo ""
echo "4️⃣  Testing PyPI collector (this may take 1-2 minutes)..."
if python3 scripts/collect-ai-pypi-packages.py; then
    echo "✅ PyPI collector test successful"
else
    echo "❌ PyPI collector test failed"
    exit 1
fi

# Check if data was inserted
echo ""
echo "5️⃣  Verifying data insertion..."
RECORD_COUNT=$(psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -t -c "SELECT COUNT(*) FROM sofia.ai_pypi_packages;" 2>/dev/null | tr -d ' ')

if [ "$RECORD_COUNT" -gt 0 ]; then
    echo "✅ Data inserted successfully ($RECORD_COUNT records in ai_pypi_packages)"
else
    echo "❌ No data found in ai_pypi_packages table"
    exit 1
fi

# Test view query
echo ""
echo "6️⃣  Testing AI Tech Radar view..."
if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -c "SELECT tech_key, display_name, hype_index FROM sofia.ai_tech_radar_consolidated ORDER BY hype_index DESC LIMIT 5;" > /dev/null 2>&1; then
    echo "✅ View query successful"
else
    echo "❌ View query failed"
    exit 1
fi

# Summary
echo ""
echo "================================================================================"
echo "✅ ALL TESTS PASSED!"
echo "================================================================================"
echo ""
echo "You can now run the full pipeline with:"
echo "  bash collect-ai-tech-radar.sh"
echo ""
echo "Or run individual collectors:"
echo "  npx tsx scripts/collect-ai-github-trends.ts"
echo "  python3 scripts/collect-ai-pypi-packages.py"
echo "  npx tsx scripts/collect-ai-npm-packages.ts"
echo "  python3 scripts/collect-ai-huggingface-models.py"
echo "  python3 scripts/collect-ai-arxiv-keywords.py"
echo ""
echo "Generate report:"
echo "  python3 analytics/ai-tech-radar-report.py"
echo "================================================================================"
