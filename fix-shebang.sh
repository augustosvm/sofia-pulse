#!/bin/bash

# Fix: Move shebang to line 1 and polyfill to line 2

FILES="collectors/jobs-collector.ts scripts/collect-arxiv-ai.ts scripts/collect-cardboard-production.ts scripts/collect-gdelt.ts scripts/collect-github-trending.ts scripts/collect-hackernews.ts scripts/collect-npm-stats.ts scripts/collect-pypi-stats.ts scripts/collect-reddit-tech.ts scripts/collect-wipo-china-patents.ts"

POLYFILL='
// Fix for Node.js 18 + undici - MUST BE AFTER SHEBANG!
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

for file in $FILES; do
    echo "🔧 Fixing $file..."

    # Extract shebang (line 12 now, should be line 1)
    SHEBANG=$(sed -n '12p' "$file")

    # Remove lines 1-12 (bad polyfill + shebang)
    tail -n +13 "$file" > "$file.tmp"

    # Build correct file: shebang + polyfill + rest
    echo "$SHEBANG" > "$file.new"
    echo "$POLYFILL" >> "$file.new"
    cat "$file.tmp" >> "$file.new"

    mv "$file.new" "$file"
    rm -f "$file.tmp"
done

echo "✅ All files fixed!"
