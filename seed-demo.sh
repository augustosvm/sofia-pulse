#!/bin/bash
#
# Seed Demo Data - Popular banco com dados históricos para demonstrar v2.0
#

set -e

echo "🌱 Sofia Pulse - Seed Demo Data"
echo "================================"
echo ""
echo "⚠️  ATENÇÃO: Este script vai inserir dados SIMULADOS no banco."
echo "   Isso é para DEMONSTRAÇÃO do v2.0 funcionando com análises avançadas."
echo ""
read -p "Continuar? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado"
    exit 1
fi

# Ativar venv-analytics
if [ ! -d "venv-analytics" ]; then
    echo "❌ venv-analytics não encontrado. Execute: bash setup-data-mining.sh"
    exit 1
fi

source venv-analytics/bin/activate

# Executar seed
echo ""
echo "🌱 Populando dados históricos..."
python3 seed-historical-data.py

echo ""
echo "✅ Seed completo!"
echo ""
echo "🚀 Agora execute:"
echo "   ./generate-insights-v2.0.sh"
echo ""
echo "   Para ver v2.0 funcionando DE VERDADE!"
