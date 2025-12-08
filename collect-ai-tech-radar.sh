#!/bin/bash
# ============================================================================
# AI Technology Radar - Complete Collection Pipeline
# ============================================================================
# Runs all AI tech collectors + analytics + report generation
#
# Sources:
#   - GitHub (AI repos and trends)
#   - PyPI (Python package downloads)
#   - NPM (JavaScript package downloads)
#   - HuggingFace (Model popularity)
#   - ArXiv (Research papers)
#
# Usage:
#   bash collect-ai-tech-radar.sh
# ============================================================================

set -e  # Exit on error

echo "================================================================================"
echo "🚀 AI TECHNOLOGY RADAR - COMPLETE COLLECTION PIPELINE"
echo "================================================================================"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "================================================================================"

# Load .env
set -a
source .env 2>/dev/null || true
set +a

# Also try to load from parent directory if running from scripts/
if [ -f "../.env" ]; then
    set -a
    source ../.env 2>/dev/null || true
    set +a
fi

# Create output directory
mkdir -p output
mkdir -p logs

# Log file
LOG_FILE="logs/ai-tech-radar-$(date +%Y%m%d-%H%M%S).log"

# Function to run a collector
run_collector() {
    local name="$1"
    local cmd="$2"

    echo ""
    echo "▶️  $name"
    echo "--------------------------------------------------------------------------------"

    if $cmd 2>&1 | tee -a "$LOG_FILE"; then
        echo "✅ $name - Success"
    else
        echo "❌ $name - Failed (continuing...)"
    fi
}

# ============================================================================
# STEP 1: Run Database Migration
# ============================================================================
echo ""
echo "📦 STEP 1: Database Migration"
echo "--------------------------------------------------------------------------------"

if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -f db/migrations/020_create_ai_tech_radar.sql 2>&1 | tee -a "$LOG_FILE"; then
    echo "✅ Migration complete"
else
    echo "⚠️  Migration failed (tables may already exist)"
fi

# Create SQL views
echo ""
echo "📊 Creating SQL views..."
if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-sofia}" -d "${DB_NAME:-sofia_db}" -f sql/04-ai-tech-radar-views.sql 2>&1 | tee -a "$LOG_FILE"; then
    echo "✅ Views created"
else
    echo "⚠️  View creation failed (views may already exist)"
fi

# ============================================================================
# STEP 2: Run Data Collectors
# ============================================================================
echo ""
echo "================================================================================"
echo "📡 STEP 2: DATA COLLECTION (5 collectors)"
echo "================================================================================"

# GitHub AI Tech Trends (TypeScript)
run_collector "GitHub AI Tech Trends" "npx tsx scripts/collect-ai-github-trends.ts"
sleep 5  # Rate limiting

# PyPI AI Packages (Python)
run_collector "PyPI AI Packages" "python3 scripts/collect-ai-pypi-packages.py"
sleep 3

# NPM AI Packages (TypeScript)
run_collector "NPM AI Packages" "npx tsx scripts/collect-ai-npm-packages.ts"
sleep 3

# HuggingFace Models (Python)
run_collector "HuggingFace AI Models" "python3 scripts/collect-ai-huggingface-models.py"
sleep 3

# ArXiv Keywords (Python)
run_collector "ArXiv AI Keywords" "python3 scripts/collect-ai-arxiv-keywords.py"

# ============================================================================
# STEP 3: Generate Analytics Report
# ============================================================================
echo ""
echo "================================================================================"
echo "📊 STEP 3: ANALYTICS & REPORT GENERATION"
echo "================================================================================"

run_collector "AI Tech Radar Report" "python3 analytics/ai-tech-radar-report.py"

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "================================================================================"
echo "✅ AI TECHNOLOGY RADAR PIPELINE COMPLETE"
echo "================================================================================"
echo "Completed: $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo ""
echo "📁 Output Files:"
echo "  - output/ai-tech-radar-report.txt"
echo "  - output/ai_tech_top20.csv"
echo "  - output/ai_tech_rising_stars.csv"
echo "  - output/ai_tech_dark_horses.csv"
echo "  - output/ai_tech_by_category.csv"
echo "  - output/ai_tech_developer_adoption.csv"
echo "  - output/ai_tech_research_interest.csv"
echo ""
echo "📋 Log file: $LOG_FILE"
echo "================================================================================"
