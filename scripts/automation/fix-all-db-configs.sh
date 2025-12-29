#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "🔧 Corrigindo DB_CONFIG em todos os scripts Python..."
echo ""

for script in analytics/correlation-papers-funding.py \
              analytics/dark-horses-report.py \
              analytics/top10-tech-trends.py \
              analytics/entity-resolution.py \
              analytics/nlg-playbooks-gemini.py; do

    if [ -f "$script" ]; then
        echo "📝 Corrigindo: $script"

        # Substituir DB_CONFIG
        sed -i "s/os.getenv('POSTGRES_HOST', 'localhost')/os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost'/g" "$script"
        sed -i "s/os.getenv('POSTGRES_PORT', '5432')/os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'/g" "$script"
        sed -i "s/os.getenv('POSTGRES_USER', 'postgres')/os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia'/g" "$script"
        sed -i "s/os.getenv('POSTGRES_PASSWORD', 'postgres')/os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or ''/g" "$script"
        sed -i "s/os.getenv('POSTGRES_DB', 'sofia_db')/os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db'/g" "$script"

        echo "   ✅ Corrigido"
    fi
done

echo ""
echo "🧪 Testando conexão..."
source venv-analytics/bin/activate

python3 test-db-connection.py

echo ""
echo "✅ Todos os scripts corrigidos!"
