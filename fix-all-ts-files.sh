#!/bin/bash

# Fix File is not defined in ALL TypeScript files that use axios/cheerio

POLYFILL='// Fix for Node.js 18 + undici - MUST BE FIRST!
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

echo "🔧 Fixing all TypeScript files with axios/cheerio imports..."
echo ""

# Find all .ts files that import axios or cheerio
FILES=$(grep -l "import.*axios\|import.*cheerio" **/*.ts 2>/dev/null || true)

for file in $FILES; do
    # Check if file already has the polyfill
    if grep -q "globalThis.File" "$file"; then
        echo "✅ $file (already has polyfill)"
    else
        echo "🔧 $file (adding polyfill)"

        # Create temp file with polyfill at the top
        echo "$POLYFILL" > "$file.tmp"
        cat "$file" >> "$file.tmp"
        mv "$file.tmp" "$file"
    fi
done

echo ""
echo "✅ All TypeScript files fixed!"
