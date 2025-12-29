#!/bin/bash

#============================================================================
# Sofia Pulse - Generate Insights (Wrapper)
#============================================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔬 Sofia Pulse - Gerador Automático de Insights"
echo ""

# Verificar se venv existe
if [ ! -d "venv-analytics" ]; then
    echo "❌ Erro: venv-analytics não encontrado"
    echo "   Execute primeiro: ./setup-data-mining.sh"
    exit 1
fi

# Ativar venv
source venv-analytics/bin/activate

# Rodar script Python
python3 generate-insights.py

echo ""
echo "🎉 Pronto! Insights gerados em analytics/insights/"
