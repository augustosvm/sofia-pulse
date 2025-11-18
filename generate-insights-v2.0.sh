#!/bin/bash
#
# Sofia Pulse - Gerar Premium Insights v2.0
# FASE 1: Base Analítica
#

set -e

echo "🚀 Sofia Pulse v2.0 - Premium Insights"
echo "======================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado"
    exit 1
fi

# Verificar psycopg2
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "⚠️  Instalando psycopg2..."
    pip3 install psycopg2-binary
fi

# Executar
echo "📊 Gerando insights v2.0..."
python3 generate-premium-insights-v2.0.py

echo ""
echo "✅ Concluído!"
echo ""
echo "📄 Ver insights:"
echo "   cat analytics/premium-insights/latest-v2.0.txt"
echo ""
echo "📧 Enviar por email:"
echo "   ./send-insights-email.sh"
