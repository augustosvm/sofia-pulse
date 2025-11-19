#!/bin/bash
set -e

echo "🔧 Corrigindo configuração de DB nos scripts Python..."
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

# Carregar .env
source .env 2>/dev/null || true

# Criar arquivo de config Python
cat > analytics/db_config.py << PYEOF
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME', 'sofia_db'),
}

# Teste
if __name__ == '__main__':
    import psycopg2
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conexão OK")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   User: {DB_CONFIG['user']}")
        print(f"   DB: {DB_CONFIG['database']}")
        conn.close()
    except Exception as e:
        print(f"❌ Erro: {e}")
PYEOF

echo "✅ Criado: analytics/db_config.py"
echo ""

# Testar conexão
source venv-analytics/bin/activate
python3 analytics/db_config.py

echo ""
echo "🔧 Atualizando scripts para usar db_config..."

# Atualizar scripts
for script in analytics/correlation-papers-funding.py \
              analytics/dark-horses-report.py \
              analytics/top10-tech-trends.py \
              analytics/entity-resolution.py \
              analytics/nlg-playbooks-gemini.py; do
    if [ -f "$script" ]; then
        # Adicionar import se não existe
        if ! grep -q "from db_config import DB_CONFIG" "$script"; then
            sed -i '/from dotenv import load_dotenv/a from db_config import DB_CONFIG' "$script"

            # Remover definição antiga de DB_CONFIG
            sed -i '/^DB_CONFIG = {/,/^}/d' "$script"

            echo "   ✅ Atualizado: $script"
        fi
    fi
done

echo ""
echo "✅ Configuração corrigida!"
