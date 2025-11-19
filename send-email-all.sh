#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "📧 Enviando relatórios completos..."
echo ""

# Carregar .env
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

EMAIL_TO="${EMAIL_TO:-augustosvm@gmail.com}"
SMTP_USER="${SMTP_USER:-augustosvm@gmail.com}"

if [ -z "$SMTP_PASS" ] || [ "$SMTP_PASS" = "your-gmail-app-password-here" ]; then
    echo "❌ SMTP_PASS não configurado no .env"
    echo ""
    echo "Configure:"
    echo "  1. Acesse: https://myaccount.google.com/apppasswords"
    echo "  2. Gere senha (16 caracteres)"
    echo "  3. Adicione no .env: SMTP_PASS=xxxx-xxxx-xxxx-xxxx"
    echo ""
    exit 1
fi

echo "📧 Destinatário: $EMAIL_TO"
echo ""

# Exportar CSVs
mkdir -p data/exports

if command -v psql &> /dev/null; then
    DB_HOST="${POSTGRES_HOST:-${DB_HOST:-localhost}}"
    DB_PORT="${POSTGRES_PORT:-${DB_PORT:-5432}}"
    DB_USER="${POSTGRES_USER:-${DB_USER:-sofia}}"
    DB_NAME="${POSTGRES_DB:-${DB_NAME:-sofia_db}}"
    DB_PASS="${POSTGRES_PASSWORD:-${DB_PASSWORD}}"

    echo "📊 Exportando CSVs..."

    # GitHub
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT language, COUNT(*) as repos, SUM(stars) as total_stars FROM sofia.github_trending WHERE language IS NOT NULL GROUP BY language ORDER BY total_stars DESC LIMIT 50) TO 'data/exports/github_trending.csv' CSV HEADER" 2>/dev/null || true

    # NPM
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT package_name, downloads_month FROM sofia.npm_stats ORDER BY downloads_month DESC LIMIT 50) TO 'data/exports/npm_stats.csv' CSV HEADER" 2>/dev/null || true

    # PyPI
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT package_name, downloads_month FROM sofia.pypi_stats ORDER BY downloads_month DESC LIMIT 50) TO 'data/exports/pypi_stats.csv' CSV HEADER" 2>/dev/null || true

    # Reddit
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT subreddit, COUNT(*) as posts FROM sofia.reddit_tech GROUP BY subreddit ORDER BY posts DESC) TO 'data/exports/reddit_stats.csv' CSV HEADER" 2>/dev/null || true

    # Funding
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT * FROM sofia.funding_rounds WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY announced_date DESC LIMIT 100) TO 'data/exports/funding_30d.csv' CSV HEADER" 2>/dev/null || true

    # Cybersecurity
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT event_type, title, severity, cvss_score, published_date, source FROM sofia.cybersecurity_events WHERE published_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY published_date DESC LIMIT 100) TO 'data/exports/cybersecurity_30d.csv' CSV HEADER" 2>/dev/null || true

    # Space Industry
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT company, mission_name, launch_date, status, rocket_type FROM sofia.space_industry ORDER BY launch_date DESC LIMIT 100) TO 'data/exports/space_launches.csv' CSV HEADER" 2>/dev/null || true

    # AI Regulation
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT title, jurisdiction, status, impact_level, announced_date FROM sofia.ai_regulation ORDER BY announced_date DESC) TO 'data/exports/ai_regulation.csv' CSV HEADER" 2>/dev/null || true

    # GDELT Events
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT event_date, actor1_name, actor2_name, goldstein_scale, avg_tone, num_mentions, action_geo_country FROM sofia.gdelt_events WHERE event_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY event_date DESC LIMIT 100) TO 'data/exports/gdelt_events_30d.csv' CSV HEADER" 2>/dev/null || true

    echo "   ✅ CSVs exportados"
fi

echo ""
echo "📧 Enviando email..."

source venv-analytics/bin/activate
python3 send-email-final.py

echo ""
echo "✅ Email enviado com sucesso!"
echo ""
echo "📧 Conteúdo:"
echo "   - Sofia Complete Report"
echo "   - Top 10 Tech Trends"
echo "   - Correlações Papers ↔ Funding"
echo "   - Dark Horses Report"
echo "   - Entity Resolution"
echo "   - NLG Playbooks (Gemini AI)"
echo "   - Special Sectors Analysis (NEW!) 🔒🚀⚖️"
echo "   - CSVs de dados RAW (incluindo Cybersecurity, Space, AI Regulation)"
echo ""
