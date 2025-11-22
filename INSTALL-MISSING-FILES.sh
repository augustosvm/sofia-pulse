#!/bin/bash
################################################################################
# INSTALL MISSING FILES - Creates migrations and Gemini key script
# These files are in .gitignore so they don't come via git pull
################################################################################

cd ~/sofia-pulse

echo "════════════════════════════════════════════════════════════════"
echo "📦 CREATING MISSING FILES"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Create migration 008
cat > migrations/008-add-city-column.sql << 'SQL_EOF'
-- Migration 008: Add city column to funding_rounds
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = 'funding_rounds' AND column_name = 'city'
    ) THEN
        ALTER TABLE sofia.funding_rounds ADD COLUMN city VARCHAR(200);
        CREATE INDEX idx_funding_rounds_city ON sofia.funding_rounds(city);
        RAISE NOTICE 'Added city column to sofia.funding_rounds';
    ELSE
        RAISE NOTICE 'Column city already exists';
    END IF;
END
$$;
COMMIT;
SQL_EOF

# Create migration 009
cat > migrations/009-add-countries-column-openalex.sql << 'SQL_EOF'
-- Migration 009: Add countries array to openalex_papers
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = 'openalex_papers' AND column_name = 'countries'
    ) THEN
        ALTER TABLE sofia.openalex_papers ADD COLUMN countries TEXT[];
        CREATE INDEX idx_openalex_papers_countries ON sofia.openalex_papers USING GIN(countries);
        RAISE NOTICE 'Added countries column to sofia.openalex_papers';
    ELSE
        RAISE NOTICE 'Column countries already exists';
    END IF;
END
$$;
COMMIT;
SQL_EOF

# Create Gemini key script
cat > apply-new-gemini-key.sh << 'KEY_EOF'
#!/bin/bash
ENV_FILE=".env"
NEW_KEY="AIzaSyA4EbO-HmToN-3U52a_ZJPYcXdXmWb8YF"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env não encontrado!"
    exit 1
fi

if grep -q "^GEMINI_API_KEY=" "$ENV_FILE"; then
    sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$NEW_KEY|" "$ENV_FILE"
    echo "✅ Chave atualizada"
else
    echo "" >> "$ENV_FILE"
    echo "GEMINI_API_KEY=$NEW_KEY" >> "$ENV_FILE"
    echo "✅ Chave adicionada"
fi

echo ""
grep "GEMINI_API_KEY" "$ENV_FILE" | sed 's/\(.\{25\}\).*/\1.../'
echo ""
echo "Restart: docker restart sofia-mastra-api"
echo ""
echo "Auto-deletando em 3s..."
sleep 3
rm -f "$0"
KEY_EOF

chmod +x apply-new-gemini-key.sh

echo "✅ Files created:"
ls -lh migrations/008-add-city-column.sql
ls -lh migrations/009-add-countries-column-openalex.sql
ls -lh apply-new-gemini-key.sh

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ DONE - Now run: bash fix-everything.sh"
echo "════════════════════════════════════════════════════════════════"
