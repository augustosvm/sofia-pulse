#!/bin/bash

#============================================================================
# Sofia Pulse - Start Jupyter Lab as Daemon
#============================================================================

# Detectar diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Iniciando Jupyter Lab como daemon..."
echo "📁 Diretório: $SCRIPT_DIR"

# Verificar se venv existe
if [ ! -d "venv-analytics" ]; then
    echo "❌ Erro: venv-analytics não encontrado em $SCRIPT_DIR"
    echo "   Execute primeiro: ./setup-data-mining.sh"
    exit 1
fi

# Ativar venv
source venv-analytics/bin/activate

# Matar instância anterior se existir
pkill -f "jupyter-lab"

# Esperar 2s
sleep 2

# Iniciar Jupyter em background
nohup jupyter lab \
  --ip=0.0.0.0 \
  --port=8889 \
  --no-browser \
  --allow-root \
  > "$SCRIPT_DIR/jupyter.log" 2>&1 &

# Esperar iniciar
sleep 3

# Mostrar token
echo ""
echo "✅ Jupyter Lab rodando em background!"
echo ""
echo "📋 Acesso:"
tail -20 "$SCRIPT_DIR/jupyter.log" | grep -o "http://.*" | head -1
echo ""
echo "🔑 Token:"
tail -20 "$SCRIPT_DIR/jupyter.log" | grep -o "token=[a-f0-9]*" | head -1
echo ""
echo "📄 Logs: tail -f $SCRIPT_DIR/jupyter.log"
echo ""
echo "🔌 Porta: 8889"
echo "🌐 URL: http://91.98.158.19:8889/lab?token=<SEU_TOKEN>"
echo ""
