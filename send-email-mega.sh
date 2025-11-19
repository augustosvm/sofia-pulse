#!/bin/bash
# ============================================================================
# SOFIA PULSE - SEND MEGA EMAIL
# ============================================================================
# Envia email com TODOS os relatórios + CSVs
# ============================================================================

set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "============================================================================"
echo "📧 SOFIA PULSE - SEND MEGA EMAIL"
echo "============================================================================"
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

# ============================================================================
# EXPORT CSVs
# ============================================================================

echo "📊 Exporting CSVs..."
mkdir -p data/exports

if command -v psql &> /dev/null; then
    DB_HOST="${POSTGRES_HOST:-${DB_HOST:-localhost}}"
    DB_PORT="${POSTGRES_PORT:-${DB_PORT:-5432}}"
    DB_USER="${POSTGRES_USER:-${DB_USER:-sofia}}"
    DB_NAME="${POSTGRES_DB:-${DB_NAME:-sofia_db}}"
    DB_PASS="${POSTGRES_PASSWORD:-${DB_PASSWORD}}"

    # GitHub
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT language, COUNT(*) as repos, SUM(stars) as total_stars FROM sofia.github_trending WHERE language IS NOT NULL GROUP BY language ORDER BY total_stars DESC LIMIT 50) TO 'data/exports/github_trending.csv' CSV HEADER" 2>/dev/null || true

    # NPM
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT package_name, downloads_month FROM sofia.npm_stats ORDER BY downloads_month DESC LIMIT 50) TO 'data/exports/npm_stats.csv' CSV HEADER" 2>/dev/null || true

    # PyPI
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT package_name, downloads_month FROM sofia.pypi_stats ORDER BY downloads_month DESC LIMIT 50) TO 'data/exports/pypi_stats.csv' CSV HEADER" 2>/dev/null || true

    # Funding (last 30 days)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT company_name, amount_usd, round_type, sector, country, announced_date FROM sofia.funding_rounds WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY announced_date DESC LIMIT 200) TO 'data/exports/funding_30d.csv' CSV HEADER" 2>/dev/null || true

    # Cybersecurity (last 30 days)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT event_type, title, severity, cvss_score, published_date, source FROM sofia.cybersecurity_events WHERE published_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY published_date DESC LIMIT 200) TO 'data/exports/cybersecurity_30d.csv' CSV HEADER" 2>/dev/null || true

    # Space launches
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT company, mission_name, launch_date, status, rocket_type FROM sofia.space_industry ORDER BY launch_date DESC LIMIT 200) TO 'data/exports/space_launches.csv' CSV HEADER" 2>/dev/null || true

    # AI Regulation
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT title, jurisdiction, status, impact_level, announced_date FROM sofia.ai_regulation ORDER BY announced_date DESC) TO 'data/exports/ai_regulation.csv' CSV HEADER" 2>/dev/null || true

    # GDELT Events (last 30 days)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT event_date, actor1_name, actor2_name, goldstein_scale, avg_tone, num_mentions, action_geo_country FROM sofia.gdelt_events WHERE event_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY event_date DESC LIMIT 200) TO 'data/exports/gdelt_events_30d.csv' CSV HEADER" 2>/dev/null || true

    # Socioeconomic - Brazil (2015-2024)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT country_name, year, indicator_name, value, unit FROM sofia.socioeconomic_indicators WHERE country_code = 'BRA' ORDER BY year DESC, indicator_name) TO 'data/exports/socioeconomic_brazil.csv' CSV HEADER" 2>/dev/null || true

    # Socioeconomic - Top 20 GDP per capita (2023)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT country_name, value as gdp_per_capita_usd FROM sofia.socioeconomic_indicators WHERE indicator_code = 'NY.GDP.PCAP.CD' AND year = 2023 ORDER BY value DESC LIMIT 20) TO 'data/exports/socioeconomic_top_gdp.csv' CSV HEADER" 2>/dev/null || true

    # Electricity consumption (latest year)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT country, year, consumption_kwh_per_capita FROM sofia.electricity_consumption ORDER BY year DESC, consumption_kwh_per_capita DESC LIMIT 200) TO 'data/exports/electricity_consumption.csv' CSV HEADER" 2>/dev/null || true

    # Commodity prices (latest)
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT commodity, price, unit, last_updated FROM sofia.commodity_prices ORDER BY last_updated DESC) TO 'data/exports/commodity_prices.csv' CSV HEADER" 2>/dev/null || true

    echo "   ✅ CSVs exportados"
fi

echo ""

# ============================================================================
# SEND EMAIL
# ============================================================================

echo "📧 Enviando email via Python..."
source venv-analytics/bin/activate
python3 send-email-mega.py

echo ""
echo "✅ Email enviado com sucesso!"
echo ""
echo "📧 Conteúdo enviado:"
echo "   📄 Relatórios TXT (10+):"
echo "      • MEGA Analysis (NEW!) - Análise cross-database completa"
echo "      • Sofia Complete Report"
echo "      • Top 10 Tech Trends"
echo "      • Correlações Papers ↔ Funding"
echo "      • Dark Horses Report"
echo "      • Entity Resolution"
echo "      • Special Sectors Analysis"
echo "      • Early-Stage Deep Dive"
echo "      • Global Energy Map"
echo "      • NLG Playbooks (Gemini AI)"
echo ""
echo "   📊 CSVs (15+):"
echo "      • github_trending.csv"
echo "      • npm_stats.csv, pypi_stats.csv"
echo "      • funding_30d.csv"
echo "      • cybersecurity_30d.csv"
echo "      • space_launches.csv"
echo "      • ai_regulation.csv"
echo "      • gdelt_events_30d.csv"
echo "      • socioeconomic_brazil.csv"
echo "      • socioeconomic_top_gdp.csv"
echo "      • electricity_consumption.csv"
echo "      • commodity_prices.csv"
echo "      • + outros..."
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
