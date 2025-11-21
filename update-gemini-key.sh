#!/bin/bash
# ============================================================================
# Update GEMINI_API_KEY in .env without overwriting other settings
# ============================================================================

ENV_FILE=".env"
GEMINI_KEY="AIzaSyCQJ7qRo5ltv5g1crYyPS8ad92fub-LuBY"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Arquivo .env não encontrado!"
    exit 1
fi

# Check if GEMINI_API_KEY already exists
if grep -q "^GEMINI_API_KEY=" "$ENV_FILE"; then
    # Update existing key
    sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEMINI_KEY|" "$ENV_FILE"
    echo "✅ GEMINI_API_KEY atualizada no .env"
else
    # Add new key
    echo "" >> "$ENV_FILE"
    echo "# Google Gemini API - For NLG Playbooks (AI-powered narratives)" >> "$ENV_FILE"
    echo "# Get free key: https://aistudio.google.com/app/apikey" >> "$ENV_FILE"
    echo "GEMINI_API_KEY=$GEMINI_KEY" >> "$ENV_FILE"
    echo "✅ GEMINI_API_KEY adicionada ao .env"
fi

echo ""
echo "Verificando configuração:"
grep "GEMINI_API_KEY" "$ENV_FILE"
