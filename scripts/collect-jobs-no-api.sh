#!/bin/bash
################################################################################
# SOFIA PULSE - Collect Jobs (No API Key Required)
# Roda todos os coletores de vagas que não precisam de API key
################################################################################

set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
cd "$SOFIA_DIR"

# Load environment
set -a
source .env 2>/dev/null || true
set +a

echo "════════════════════════════════════════════════════════════════"
echo "💼 SOFIA PULSE - JOB COLLECTORS (No API)"
echo "════════════════════════════════════════════════════════════════"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

TOTAL_JOBS=0

# 1. Arbeitnow (Europe)
echo "────────────────────────────────────────────────────────────────"
echo "🇪🇺 [1/4] Arbeitnow (Europe)"
echo "────────────────────────────────────────────────────────────────"
if npx tsx scripts/collect-jobs-arbeitnow.ts; then
    echo "✅ Arbeitnow completed"
else
    echo "⚠️  Arbeitnow failed"
fi
echo ""

# 2. The Muse (with salary data)
echo "────────────────────────────────────────────────────────────────"
echo "🎨 [2/4] The Muse (Salary data)"
echo "────────────────────────────────────────────────────────────────"
if npx tsx scripts/collect-jobs-themuse.ts; then
    echo "✅ The Muse completed"
else
    echo "⚠️  The Muse failed"
fi
echo ""

# 3. Remotive (already working)
echo "────────────────────────────────────────────────────────────────"
echo "🌍 [2/3] Remotive (Remote-first)"
echo "────────────────────────────────────────────────────────────────"
if npx tsx scripts/collect-jobs-api-only.ts; then
    echo "✅ Remotive completed"
else
    echo "⚠️  Remotive failed"
fi
echo ""

# 3. GitHub Jobs (if exists)
echo "────────────────────────────────────────────────────────────────"
echo "💻 [3/3] GitHub Jobs"
echo "────────────────────────────────────────────────────────────────"
if [ -f "scripts/collect-jobs-github.ts" ]; then
    if npx tsx scripts/collect-jobs-github.ts; then
        echo "✅ GitHub Jobs completed"
    else
        echo "⚠️  GitHub Jobs failed"
    fi
else
    echo "⏭️  GitHub Jobs collector not found (skipping)"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "📊 SUMMARY"
echo "════════════════════════════════════════════════════════════════"

# Get total jobs from last 24h
STATS=$(docker exec -i sofia-postgres psql -U sofia -d sofia_db -t << 'EOF'
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT company) as companies,
    COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote,
    COUNT(CASE WHEN collected_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h
FROM sofia.tech_jobs;
EOF
)

echo "$STATS" | while read total companies remote last_24h; do
    echo "Total jobs in DB: $total"
    echo "Unique companies: $companies"
    echo "Remote positions: $remote"
    echo "Collected last 24h: $last_24h"
done

echo ""
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════════════════════════"
