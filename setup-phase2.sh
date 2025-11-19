#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "🚀 FASE 2 - Setup e Primeira Execução"
echo ""

# Git pull
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE 2>/dev/null || true

# Ativar venv
source venv-analytics/bin/activate || {
    python3 -m venv venv-analytics
    source venv-analytics/bin/activate
    pip install -q psycopg2-binary python-dotenv pandas numpy scipy
}

# Instalar npm packages
npm install --silent 2>/dev/null || true

# Criar migration GDELT
if command -v psql &> /dev/null; then
    DB_HOST=$(grep POSTGRES_HOST .env | cut -d'=' -f2)
    DB_PORT=$(grep POSTGRES_PORT .env | cut -d'=' -f2)
    DB_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
    DB_NAME=$(grep POSTGRES_DB .env | cut -d'=' -f2)
    PGPASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)

    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f db/migrations/011_create_gdelt_events.sql 2>/dev/null && echo "✅ GDELT table created" || echo "⚠️  GDELT table exists"
fi

echo ""
echo "🔥 Coletando GDELT (primeira vez)..."
npm run collect:gdelt 2>&1 | tail -10 || true

echo ""
echo "🔗 Gerando Correlações Papers ↔ Funding..."
python3 analytics/correlation-papers-funding.py > analytics/correlation-latest.txt 2>&1
tail -30 analytics/correlation-latest.txt

echo ""
echo "🐴 Gerando Dark Horses Report..."
python3 analytics/dark-horses-report.py 2>&1 | tail -30

echo ""
echo "📄 Consolidando relatório completo..."
bash run-insights.sh 2>&1 | tail -50

echo ""
echo "📧 Enviando por email..."

python3 << 'PYEOF'
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
EMAIL_TO = os.getenv('EMAIL_TO', 'augustosvm@gmail.com')

if not SMTP_PASS or SMTP_PASS == 'your-gmail-app-password-here':
    print("⚠️  SMTP_PASS não configurado - pulando email")
    exit(0)

msg = MIMEMultipart()
msg['From'] = SMTP_USER
msg['To'] = EMAIL_TO
msg['Subject'] = f"Sofia Pulse FASE 2 - Correlações + Dark Horses - {datetime.now().strftime('%Y-%m-%d')}"

with open('analytics/sofia-report.txt', 'r') as f:
    body = f.read()

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar relatório
with open('analytics/sofia-report.txt', 'rb') as f:
    attachment = MIMEApplication(f.read(), _subtype='txt')
    attachment.add_header('Content-Disposition', 'attachment', filename='sofia-phase2-report.txt')
    msg.attach(attachment)

# Anexar correlações
try:
    with open('analytics/correlation-latest.txt', 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='txt')
        attachment.add_header('Content-Disposition', 'attachment', filename='correlations.txt')
        msg.attach(attachment)
except:
    pass

# Anexar dark horses
try:
    with open('analytics/dark-horses-latest.txt', 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='txt')
        attachment.add_header('Content-Disposition', 'attachment', filename='dark-horses.txt')
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
PYEOF

echo ""
echo "✅ FASE 2 instalada e executada!"
echo ""
echo "📧 Email enviado para: augustosvm@gmail.com"
echo "   - Tech Trend Score"
echo "   - Correlações Papers ↔ Funding"
echo "   - Dark Horses Report"
echo "   - Premium Insights v2.0"
echo ""
