#!/bin/bash
#
# Sofia Pulse - Cron Wrapper
# Garante que env vars são carregadas antes de executar scripts Python
#

set -e

# Diretório do projeto
PROJECT_DIR="/Users/augustovespermann/sofia-pulse"
cd "$PROJECT_DIR" || exit 1

# Carregar env vars do .env
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# DATABASE_URL obrigatório - SEM FALLBACK
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERRO CRÍTICO: DATABASE_URL não configurado"
    echo "   Configure em .env: DATABASE_URL=postgresql://user:pass@host:port/dbname"
    exit 1
fi

# Ativar venv
source "$PROJECT_DIR/.venv/bin/activate"

# Executar comando passado como argumento
exec "$@"
