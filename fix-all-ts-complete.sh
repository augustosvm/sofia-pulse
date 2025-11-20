#!/bin/bash

# Fix ALL TypeScript files in the project

echo "🔧 Adding File polyfill to ALL TypeScript files..."
echo ""

# All TS files from run-mega-collection.sh
ALL_TS_FILES="
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

POLYFILL='// Fix for Node.js 18 + undici - MUST BE AFTER SHEBANG!
// @ts-ignore
if (typeof File === '\''undefined'\'') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}
'

for file in $ALL_TS_FILES; do
    if [ ! -f "$file" ]; then
        echo "⚠️  $file (not found, skipping)"
        continue
    fi

    # Check if already has polyfill
    if grep -q "globalThis.File" "$file"; then
        echo "✅ $file (already fixed)"
        continue
    fi

    echo "🔧 $file (adding polyfill)"

    # Check if has shebang
    FIRST_LINE=$(head -1 "$file")
    if [[ "$FIRST_LINE" == "#!/"* ]]; then
        # Has shebang: keep it, add polyfill after
        {
            echo "$FIRST_LINE"
            echo ""
            echo "$POLYFILL"
            tail -n +2 "$file"
        } > "$file.tmp"
    else
        # No shebang: add polyfill at top
        {
            echo "$POLYFILL"
            cat "$file"
        } > "$file.tmp"
    fi

    mv "$file.tmp" "$file"
done

echo ""
echo "✅ All TypeScript files processed!"
