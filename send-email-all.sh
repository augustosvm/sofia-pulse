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

    echo "   ✅ CSVs exportados"
fi

echo ""
echo "📧 Enviando email..."

source venv-analytics/bin/activate

python3 << 'PYEOF'
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import glob

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
EMAIL_TO = os.getenv('EMAIL_TO')

msg = MIMEMultipart()
msg['From'] = SMTP_USER
msg['To'] = EMAIL_TO
msg['Subject'] = f"Sofia Pulse COMPLETE Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"

body = f"""SOFIA PULSE - COMPLETE INTELLIGENCE REPORT
{'='*80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Recipient: {EMAIL_TO}

{'='*80}

Este relatório contém TODAS as análises:

📊 DADOS COLETADOS:
- GitHub Trending (53 tecnologias)
- HackerNews (3 tecnologias)
- Reddit Tech (6 subreddits)
- NPM Stats (30+ packages)
- PyPI Stats (26+ packages Python)
- GDELT (eventos geopolíticos)
- Papers (ArXiv, OpenAlex)
- Funding Rounds
- B3, NASDAQ

📈 ANÁLISES INCLUÍDAS:
- Tech Trend Score (ranking completo)
- Top 10 Tech Trends (semanal)
- Correlações Papers ↔ Funding (lag analysis)
- Dark Horses Report (oportunidades)
- Entity Resolution (fuzzy matching)
- NLG Playbooks (Gemini AI)
- Premium Insights v2.0 (regional + temporal)

📁 ANEXOS:
- Relatórios completos (TXT)
- Dados RAW (CSVs)

Veja os anexos abaixo.

{'='*80}
"""

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar relatórios
reports = [
    ('analytics/sofia-report.txt', 'sofia-complete-report.txt'),
    ('analytics/top10-latest.txt', 'top10-tech-trends.txt'),
    ('analytics/correlation-latest.txt', 'correlations-papers-funding.txt'),
    ('analytics/dark-horses-latest.txt', 'dark-horses-report.txt'),
    ('analytics/entity-resolution-latest.txt', 'entity-resolution.txt'),
    ('analytics/playbook-latest.txt', 'nlg-playbooks-gemini.txt'),
]

for file_path, file_name in reports:
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='txt')
            attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
            msg.attach(attachment)

# Anexar CSVs
for csv_file in glob.glob('data/exports/*.csv'):
    try:
        with open(csv_file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='csv')
            filename = os.path.basename(csv_file)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
    except:
        pass

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()
    print(f"✅ Email enviado para {EMAIL_TO}")
except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")
    exit(1)
PYEOF

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
echo "   - CSVs de dados RAW"
echo ""
