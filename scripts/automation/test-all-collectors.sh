#!/bin/bash

# Test each TypeScript collector individually to find which one fails

echo "🔍 Testando cada collector TypeScript individualmente..."
echo ""

COLLECTORS="
collectors/ipo-calendar.ts
finance/scripts/collect-brazil-stocks.ts
finance/scripts/collect-funding-rounds.ts
finance/scripts/collect-nasdaq-momentum.ts
scripts/collect-ai-companies.ts
scripts/collect-ai-regulation.ts
scripts/collect-arxiv-ai.ts
scripts/collect-asia-universities.ts
scripts/collect-cardboard-production.ts
scripts/collect-cybersecurity.ts
scripts/collect-epo-patents.ts
scripts/collect-gdelt.ts
scripts/collect-github-trending.ts
scripts/collect-hackernews.ts
scripts/collect-hkex-ipos.ts
scripts/collect-nih-grants.ts
scripts/collect-npm-stats.ts
scripts/collect-openalex.ts
scripts/collect-pypi-stats.ts
scripts/collect-reddit-tech.ts
scripts/collect-space-industry.ts
scripts/collect-wipo-china-patents.ts
"

FAILED=()

for file in $COLLECTORS; do
    echo -n "Testing $file... "

    if timeout 10 npx tsx "$file" > /dev/null 2>&1; then
        echo "✅ OK"
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo "⏱️  TIMEOUT (OK - provavelmente funcionando)"
        else
            echo "❌ FAILED"
            FAILED+=("$file")

            # Run again to see error
            echo "   Error output:"
            npx tsx "$file" 2>&1 | grep -A2 "File is not defined" | head -5 | sed 's/^/   /'
        fi
    fi
done

echo ""
echo "═══════════════════════════════════════════════════"
if [ ${#FAILED[@]} -eq 0 ]; then
    echo "✅ Todos os collectors passaram!"
else
    echo "❌ Collectors com erro (${#FAILED[@]}):"
    for f in "${FAILED[@]}"; do
        echo "   - $f"
    done
fi
