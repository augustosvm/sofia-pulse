#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - INSTALAÇÃO COMPLETA (TUDO)"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

# Git pull
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE 2>&1 | head -5 || true

# Venv
if [ ! -d "venv-analytics" ]; then
    python3 -m venv venv-analytics
fi
source venv-analytics/bin/activate
pip install -q psycopg2-binary python-dotenv pandas numpy scipy google-generativeai

# NPM
npm install --silent 2>/dev/null || true

# Migrations
if command -v psql &> /dev/null; then
    DB_HOST=$(grep POSTGRES_HOST .env | cut -d'=' -f2 || echo "localhost")
    DB_PORT=$(grep POSTGRES_PORT .env | cut -d'=' -f2 || echo "5432")
    DB_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2 || echo "sofia")
    DB_NAME=$(grep POSTGRES_DB .env | cut -d'=' -f2 || echo "sofia_db")
    PGPASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)

    for migration in db/migrations/012_create_reddit_tech.sql \
                     db/migrations/013_create_npm_stats.sql \
                     db/migrations/014_create_pypi_stats.sql; do
        if [ -f "$migration" ]; then
            PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                -f "$migration" 2>&1 | grep -E "(CREATE|ERROR)" || true
        fi
    done
fi

echo ""
echo "🔥 Coletando dados (primeira vez)..."
echo ""

npm run collect:reddit 2>&1 | tail -10 || true
sleep 2
npm run collect:npm-stats 2>&1 | tail -10 || true
sleep 2
npm run collect:pypi-stats 2>&1 | tail -10 || true

echo ""
echo "📊 Gerando análises..."
echo ""

python3 analytics/top10-tech-trends.py > analytics/top10-latest.txt 2>&1
tail -30 analytics/top10-latest.txt

python3 analytics/entity-resolution.py > analytics/entity-resolution-latest.txt 2>&1
python3 analytics/nlg-playbooks-gemini.py 2>&1 | tail -20

echo ""
echo "📧 Enviando email..."
echo ""

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
SMTP_USER = os.getenv('SMTP_USER', 'augustosvm@gmail.com')
SMTP_PASS = os.getenv('SMTP_PASS', '')
EMAIL_TO = os.getenv('EMAIL_TO', 'augustosvm@gmail.com')

if not SMTP_PASS or SMTP_PASS == 'your-gmail-app-password-here':
    print("⚠️  SMTP não configurado - pulando email")
    exit(0)

msg = MIMEMultipart()
msg['From'] = SMTP_USER
msg['To'] = EMAIL_TO
msg['Subject'] = f"Sofia Pulse COMPLETE Report - {datetime.now().strftime('%Y-%m-%d')}"

body = f"""SOFIA PULSE - COMPLETE INTELLIGENCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Este email contém TODOS os relatórios:
- Sofia Complete Report (Tech Trends + Correlações + Dark Horses)
- Top 10 Tech Trends (semanal)
- Entity Resolution
- NLG Playbooks (Gemini AI)
- CSVs de dados RAW

Veja os anexos.
"""

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar relatórios
files = [
    'analytics/sofia-report.txt',
    'analytics/top10-latest.txt',
    'analytics/entity-resolution-latest.txt',
    'analytics/playbook-latest.txt',
    'analytics/correlation-latest.txt',
    'analytics/dark-horses-latest.txt',
]

for file in files:
    if os.path.exists(file):
        with open(file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='txt')
            filename = os.path.basename(file)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)

# CSVs
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
    print(f"❌ Erro: {e}")
PYEOF

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ INSTALAÇÃO COMPLETA!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📧 Email enviado para: augustosvm@gmail.com"
echo ""
echo "📊 Relatórios gerados:"
echo "   - Sofia Complete Report"
echo "   - Top 10 Tech Trends"
echo "   - Correlações Papers ↔ Funding"
echo "   - Dark Horses"
echo "   - Entity Resolution"
echo "   - NLG Playbooks (Gemini AI)"
echo ""
echo "✅ Pronto!"
echo ""
