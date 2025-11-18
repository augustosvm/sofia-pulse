#!/bin/bash

###############################################################################
# Sofia Pulse - Configurar SMTP Password
# Adiciona senha do Gmail automaticamente
###############################################################################

set -e

# Detectar diretório
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔐 Configurando SMTP Password..."

# Senha do Gmail App Password
SMTP_PASS="msnxttcudgfhveel"

# Atualizar .env
if [ -f ".env" ]; then
    # Verificar se SMTP_PASS já existe
    if grep -q "^SMTP_PASS=" .env; then
        # Atualizar existente
        sed -i "s/^SMTP_PASS=.*/SMTP_PASS=$SMTP_PASS/" .env
        echo "✅ SMTP_PASS atualizado no .env"
    else
        # Adicionar novo
        echo "SMTP_PASS=$SMTP_PASS" >> .env
        echo "✅ SMTP_PASS adicionado ao .env"
    fi
else
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

echo ""
echo "✅ Configuração completa!"
echo "📧 Email configurado: augustosvm@gmail.com"
echo "🔐 SMTP Password: configurado"
echo ""
echo "Teste o envio de email:"
echo "  bash send-insights-email.sh"
