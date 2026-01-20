
OUTPUT="🐍 Legacy Python Collectors Loaded: 716
🚀 Starting GDELT Events...
============================================================
📋 Fetching from https://api.gdeltproject.org/api/v2/doc/doc...
🔄 Parsing response...
   ✅ Parsed 60 items
💾 Inserting into sofia.industry_signals...
✅ Collection complete: 60 items (Unified Table)."

echo "Regex 1 (Inserted):"
echo "$OUTPUT" | grep -oP '✅ Inserted \K\d+' | head -1

echo "Regex 2 (Saved):"
echo "$OUTPUT" | grep -oP '✅ Saved \K\d+' | head -1

echo "Regex 3 (Collected):"
echo "$OUTPUT" | grep -oP '✅ Collected: \K\d+' | head -1

echo "Regex 4 (novos registros):"
echo "$OUTPUT" | grep -oP '\K\d+ novos registros' | grep -oP '^\d+' | head -1
