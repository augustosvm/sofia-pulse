#!/bin/bash
# ============================================================================
# Update GEMINI_API_KEY in .env without overwriting other settings
# Usage: ./update-gemini-key.sh <NEW_API_KEY>
# ============================================================================

if [ -z "$1" ]; then
    echo "❌ Erro: Chave API não fornecida"
    echo ""
    echo "Uso: ./update-gemini-key.sh <GEMINI_API_KEY>"
    echo ""
    echo "Exemplo:"
    echo "  ./update-gemini-key.sh AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    echo ""
    echo "Obter chave em: https://aistudio.google.com/app/apikey"
    exit 1
fi

ENV_FILE=".env"
GEMINI_KEY="$1"

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
