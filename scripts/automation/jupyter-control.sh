#!/bin/bash

#============================================================================
# Sofia Pulse - Jupyter Lab Control
#============================================================================

case "$1" in
  start)
    echo "🚀 Iniciando Jupyter Lab..."
    sudo systemctl start jupyter-lab
    sleep 2
    sudo systemctl status jupyter-lab --no-pager
    echo ""
    echo "📋 Token:"
    tail -20 ~/jupyter.log | grep -o "token=[a-f0-9]*" | head -1
    ;;

  stop)
    echo "🛑 Parando Jupyter Lab..."
    sudo systemctl stop jupyter-lab
    ;;

  restart)
    echo "🔄 Reiniciando Jupyter Lab..."
    sudo systemctl restart jupyter-lab
    sleep 2
    sudo systemctl status jupyter-lab --no-pager
    echo ""
    echo "📋 Token:"
    tail -20 ~/jupyter.log | grep -o "token=[a-f0-9]*" | head -1
    ;;

  status)
    sudo systemctl status jupyter-lab --no-pager
    echo ""
    echo "📋 Token:"
    tail -20 ~/jupyter.log | grep -o "token=[a-f0-9]*" | head -1
    ;;

  token)
    echo "🔑 Token do Jupyter Lab:"
    tail -50 ~/jupyter.log | grep -o "http://.*token=[a-f0-9]*" | head -1
    ;;

  logs)
    echo "📄 Logs do Jupyter Lab (Ctrl+C para sair):"
    tail -f ~/jupyter.log
    ;;

  enable)
    echo "⚙️  Habilitando auto-start do Jupyter..."
    sudo systemctl enable jupyter-lab
    echo "✅ Jupyter vai iniciar automaticamente no boot!"
    ;;

  disable)
    echo "⚙️  Desabilitando auto-start do Jupyter..."
    sudo systemctl disable jupyter-lab
    ;;

  *)
    echo "Sofia Pulse - Jupyter Lab Control"
    echo ""
    echo "Uso: $0 {start|stop|restart|status|token|logs|enable|disable}"
    echo ""
    echo "Comandos:"
    echo "  start    - Inicia o Jupyter Lab"
    echo "  stop     - Para o Jupyter Lab"
    echo "  restart  - Reinicia o Jupyter Lab"
    echo "  status   - Mostra status do serviço"
    echo "  token    - Mostra token de acesso"
    echo "  logs     - Mostra logs em tempo real"
    echo "  enable   - Auto-start no boot"
    echo "  disable  - Desabilita auto-start"
    exit 1
    ;;
esac
