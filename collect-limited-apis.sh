#!/bin/bash

################################################################################
# Sofia Pulse - Limited APIs Collection
################################################################################
#
# Coleta dados de APIs COM rate limit severo
# Executa: 13:00 BRT / 16:00 UTC
#
# APIs incluídas:
# - GitHub (60/hora sem token, 5000/hora com token)
# - Reddit (60/minuto)
# - OpenAlex, NIH (rate limited)
#
# IMPORTANTE: Usa rate limiter automático com exponential backoff
#
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "⚡ SOFIA PULSE - LIMITED APIs COLLECTION"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "📡 Collecting from rate-limited APIs"
echo "🔄 Using automatic retry with exponential backoff"
echo ""

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  WARNING: GITHUB_TOKEN not set!"
    echo "   Rate limit: 60 requests/hour (unauthenticated)"
    echo "   Add GITHUB_TOKEN to .env for 5000 requests/hour"
    echo ""
else
    echo "✅ GITHUB_TOKEN detected (5000 requests/hour)"
    echo ""
fi

################################################################################
# GITHUB COLLECTORS (with rate limiting)
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "🐙 GITHUB COLLECTORS (Rate Limited)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣  GitHub Trending (with rate limiter)..."
npx tsx scripts/collect-github-trending.ts || echo "⚠️  Failed"

echo ""
echo "⏳ Waiting 60s before next GitHub collector..."
sleep 60

echo ""
echo "2️⃣  GitHub Niches (with rate limiter)..."
npx tsx scripts/collect-github-niches.ts || echo "⚠️  Failed"

################################################################################
# REDDIT COLLECTORS (60/minute limit)
################################################################################

echo ""
echo "⏳ Waiting 60s before Reddit collector..."
sleep 60

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🤖 REDDIT COLLECTOR (60/minute limit)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "3️⃣  Reddit Tech Subreddits (with rate limiter)..."
npx tsx scripts/collect-reddit-tech.ts || echo "⚠️  Failed"

################################################################################
# RESEARCH COLLECTORS (some with rate limits)
################################################################################

echo ""
echo "⏳ Waiting 60s before research collectors..."
sleep 60

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📚 RESEARCH COLLECTORS (Rate Limited)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "4️⃣  OpenAlex Papers (API has limits)..."
npx tsx scripts/collect-openalex.ts || echo "⚠️  Failed"

echo ""
echo "⏳ Waiting 60s..."
sleep 60

echo ""
echo "5️⃣  NIH Grants (API has limits)..."
npx tsx scripts/collect-nih-grants.ts || echo "⚠️  Failed"

echo ""
echo "⏳ Waiting 60s..."
sleep 60

echo ""
echo "6️⃣  Asia Universities (web scraping, conservative)..."
npx tsx scripts/collect-asia-universities.ts || echo "⚠️  Failed"

################################################################################
# OTHER LIMITED APIs
################################################################################

echo ""
echo "⏳ Waiting 60s..."
sleep 60

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🌍 OTHER LIMITED APIs"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "7️⃣  GDELT Geopolitical Events..."
npx tsx scripts/collect-gdelt.ts || echo "⚠️  Failed"

echo ""
echo "⏳ Waiting 60s..."
sleep 60

echo ""
echo "8️⃣  AI Regulation Tracker..."
npx tsx scripts/collect-ai-regulation.ts || echo "⚠️  Failed"

echo ""
echo "⏳ Waiting 60s..."
sleep 60

echo ""
echo "9️⃣  EPO Patents (Europe)..."
npx tsx scripts/collect-epo-patents.ts || echo "⚠️  Failed"

echo ""
echo "⏳ Waiting 60s..."
sleep 60

echo ""
echo "🔟 WIPO China Patents..."
npx tsx scripts/collect-wipo-china-patents.ts || echo "⚠️  Failed"

################################################################################
# SUMMARY
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ LIMITED APIs COLLECTION COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⏱️  Completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "📊 Collectors Run: 10"
echo "🔄 All with automatic retry and exponential backoff"
echo "⏱️  Total time: ~10 minutes (with delays)"
echo ""
echo "🎯 Next Step: Run analytics at 22:00 UTC"
echo ""
