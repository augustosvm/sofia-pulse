#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

source .env 2>/dev/null || true

EMAIL_TO="${EMAIL_TO:-augustosvm@gmail.com}"
SMTP_USER="${SMTP_USER:-augustosvm@gmail.com}"

if [ -z "$SMTP_PASS" ] || [ "$SMTP_PASS" = "your-gmail-app-password-here" ]; then
    echo "❌ SMTP_PASS não configurado no .env"
    exit 1
fi

echo "📧 Enviando FASE 2 para: $EMAIL_TO"
echo ""

# Exportar CSVs
mkdir -p data/exports

if command -v psql &> /dev/null; then
    DB_HOST="${POSTGRES_HOST:-localhost}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    DB_USER="${POSTGRES_USER:-sofia}"
    DB_NAME="${POSTGRES_DB:-sofia_db}"

    # GitHub
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT language, COUNT(*) as repos, SUM(stars) as total_stars FROM sofia.github_trending WHERE language IS NOT NULL GROUP BY language ORDER BY total_stars DESC LIMIT 50) TO 'data/exports/github_trending.csv' CSV HEADER" 2>/dev/null || true

    # HackerNews
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT unnest(mentioned_technologies) as tech, COUNT(*) as mentions FROM sofia.hackernews_stories GROUP BY tech ORDER BY mentions DESC LIMIT 50) TO 'data/exports/hackernews_tech.csv' CSV HEADER" 2>/dev/null || true

    # GDELT
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT event_date, actor1_country, avg_tone, num_articles, categories FROM sofia.gdelt_events WHERE event_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY event_date DESC LIMIT 100) TO 'data/exports/gdelt_events.csv' CSV HEADER" 2>/dev/null || true

    # Funding
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT * FROM sofia.funding_rounds WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY announced_date DESC) TO 'data/exports/funding_30d.csv' CSV HEADER" 2>/dev/null || true
fi

# Enviar email
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
msg['Subject'] = f"Sofia Pulse Intelligence Report (FASE 2) - {datetime.now().strftime('%Y-%m-%d')}"

# Corpo
with open('analytics/sofia-report.txt', 'r') as f:
    body = f.read()

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar relatório principal
with open('analytics/sofia-report.txt', 'rb') as f:
    attachment = MIMEApplication(f.read(), _subtype='txt')
    attachment.add_header('Content-Disposition', 'attachment', filename='sofia-complete-report.txt')
    msg.attach(attachment)

# Anexar correlações
if os.path.exists('analytics/correlation-latest.txt'):
    with open('analytics/correlation-latest.txt', 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='txt')
        attachment.add_header('Content-Disposition', 'attachment', filename='correlations-papers-funding.txt')
        msg.attach(attachment)

# Anexar dark horses
if os.path.exists('analytics/dark-horses-latest.txt'):
    with open('analytics/dark-horses-latest.txt', 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='txt')
        attachment.add_header('Content-Disposition', 'attachment', filename='dark-horses-report.txt')
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

# Enviar
try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()
    print(f"✅ Email enviado para {EMAIL_TO}")
    print("")
    print("📧 Conteúdo enviado:")
    print("   - Sofia Complete Report (TXT)")
    print("   - Correlações Papers ↔ Funding (TXT)")
    print("   - Dark Horses Report (TXT)")
    print("   - CSVs de dados RAW")
except Exception as e:
    print(f"❌ Erro: {e}")
    exit(1)
PYEOF

echo ""
echo "✅ Email enviado!"
