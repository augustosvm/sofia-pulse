#!/bin/bash
# Roda Causal Insights com venv correto

cd "$(dirname "$0")"

echo "🔥 SOFIA PULSE - CAUSAL INSIGHTS ML"
echo ""

# Ativar venv Python
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ venv não encontrado. Criando..."
    python3 -m venv venv-analytics
    source venv-analytics/bin/activate
    pip install psycopg2-binary python-dotenv > /dev/null 2>&1
fi

# Rodar análise
python3 analytics/causal-insights-ml.py

echo ""
echo "✅ Relatório salvo em: analytics/causal-insights-latest.txt"
