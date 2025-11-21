#!/bin/bash
# Configure Gemini API Key for NLG Playbooks

echo "========================================="
echo "🤖 SOFIA PULSE - Gemini AI Configuration"
echo "========================================="
echo ""
echo "NLG Playbooks usa Gemini AI para gerar narrativas inteligentes"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "💡 Criando .env a partir de .env.example..."
    cp .env.example .env 2>/dev/null || touch .env
fi

# Check if key already exists
if grep -q "GEMINI_API_KEY=" .env; then
    CURRENT_KEY=$(grep "GEMINI_API_KEY=" .env | cut -d'=' -f2)
    if [ -n "$CURRENT_KEY" ] && [ "$CURRENT_KEY" != "your_gemini_key_here" ]; then
        echo "✅ GEMINI_API_KEY já configurada: ${CURRENT_KEY:0:20}..."
        echo ""
        read -p "Deseja substituir? (y/N): " REPLACE
        if [ "$REPLACE" != "y" ] && [ "$REPLACE" != "Y" ]; then
            echo "❌ Operação cancelada"
            exit 0
        fi
    fi
fi

echo ""
echo "📝 Para obter sua chave Gemini AI:"
echo "   1. Acesse: https://aistudio.google.com/app/apikey"
echo "   2. Clique em 'Get API key' ou 'Create API key'"
echo "   3. Copie a chave gerada"
echo ""
read -p "Cole sua GEMINI_API_KEY aqui: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "❌ Nenhuma chave fornecida"
    exit 1
fi

# Remove existing key
sed -i '/GEMINI_API_KEY=/d' .env

# Add new key
echo "GEMINI_API_KEY=$API_KEY" >> .env

echo ""
echo "✅ GEMINI_API_KEY configurada com sucesso!"
echo ""
echo "🚀 Agora você pode usar NLG Playbooks:"
echo "   python3 analytics/nlg-playbooks-gemini.py"
echo ""
echo "💡 Ou rodar analytics completo:"
echo "   bash run-mega-analytics.sh"
echo ""
