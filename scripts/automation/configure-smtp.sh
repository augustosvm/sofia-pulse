#!/bin/bash

###############################################################################
# Sofia Pulse - Configurar TODAS as credenciais
# Restaura SMTP + API Keys automaticamente
###############################################################################

set -e

# Detectar diretório
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔐 Configurando credenciais completas..."

# SMTP Password
SMTP_PASS="msnxttcudgfhveel"

# API Keys
ALPHA_KEY="JFVYRODTWGO1W5M6"
EIA_KEY="QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys"
NINJAS_KEY="IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I"

# Atualizar .env
if [ -f ".env" ]; then
    # SMTP
    if grep -q "^SMTP_PASS=" .env; then
        sed -i "s|^SMTP_PASS=.*|SMTP_PASS=$SMTP_PASS|" .env
        echo "✅ SMTP_PASS atualizado"
    else
        echo "SMTP_PASS=$SMTP_PASS" >> .env
        echo "✅ SMTP_PASS adicionado"
    fi

    if grep -q "^SMTP_USER=" .env; then
        sed -i "s|^SMTP_USER=.*|SMTP_USER=augustosvm@gmail.com|" .env
    else
        echo "SMTP_USER=augustosvm@gmail.com" >> .env
    fi

    # Alpha Vantage
    if grep -q "^ALPHA_VANTAGE_API_KEY=" .env; then
        sed -i "s|^ALPHA_VANTAGE_API_KEY=.*|ALPHA_VANTAGE_API_KEY=$ALPHA_KEY|" .env
        echo "✅ ALPHA_VANTAGE_API_KEY atualizado"
    else
        echo "ALPHA_VANTAGE_API_KEY=$ALPHA_KEY" >> .env
        echo "✅ ALPHA_VANTAGE_API_KEY adicionado"
    fi

    # EIA
    if grep -q "^EIA_API_KEY=" .env; then
        sed -i "s|^EIA_API_KEY=.*|EIA_API_KEY=$EIA_KEY|" .env
        echo "✅ EIA_API_KEY atualizado"
    else
        echo "EIA_API_KEY=$EIA_KEY" >> .env
        echo "✅ EIA_API_KEY adicionado"
    fi

    # API Ninjas
    if grep -q "^API_NINJAS_KEY=" .env; then
        sed -i "s|^API_NINJAS_KEY=.*|API_NINJAS_KEY=$NINJAS_KEY|" .env
        echo "✅ API_NINJAS_KEY atualizado"
    else
        echo "API_NINJAS_KEY=$NINJAS_KEY" >> .env
        echo "✅ API_NINJAS_KEY adicionado"
    fi

    # Gemini
    GEMINI_KEY="AIzaSyAS1uHXDupa5nEzbpnq7BGrZ4M-iD9nsv8"
    if grep -q "^GEMINI_API_KEY=" .env; then
        sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEMINI_KEY|" .env
        echo "✅ GEMINI_API_KEY atualizado"
    else
        echo "GEMINI_API_KEY=$GEMINI_KEY" >> .env
        echo "✅ GEMINI_API_KEY adicionado"
    fi

    # GitHub Token (opcional - aumenta rate limit de 60/h para 5000/h)
    # Se não tiver, adiciona placeholder
    if ! grep -q "^GITHUB_TOKEN=" .env; then
        echo "GITHUB_TOKEN=your-github-token-here" >> .env
        echo "⚠️  GITHUB_TOKEN placeholder adicionado (configure manualmente)"
    fi
else
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

echo ""
echo "✅ Configuração completa!"
echo "📧 Email: augustosvm@gmail.com"
echo "🔐 SMTP: configurado"
echo "🔑 Alpha Vantage: ${ALPHA_KEY:0:15}..."
echo "🔑 EIA: ${EIA_KEY:0:15}..."
echo "🔑 API Ninjas: ${NINJAS_KEY:0:15}..."
echo "🔑 Gemini: ${GEMINI_KEY:0:15}..."
echo ""
