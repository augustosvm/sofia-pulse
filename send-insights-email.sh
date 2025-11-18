#!/bin/bash

###############################################################################
# Sofia Pulse - Email Sender de Insights
# Envia insights + arquivos de dados raw por email
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}📧 Sofia Pulse - Email Sender${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
    echo -e "${YELLOW}Crie um arquivo .env com:${NC}"
    echo "EMAIL_TO=seu-email@example.com"
    echo "EMAIL_FROM=sofia-pulse@seu-dominio.com"
    echo "SMTP_HOST=smtp.gmail.com"
    echo "SMTP_PORT=587"
    echo "SMTP_USER=seu-email@gmail.com"
    echo "SMTP_PASS=sua-senha-app"
    exit 1
fi

# Carregar variáveis
source .env

# Verificar variáveis necessárias
if [ -z "$EMAIL_TO" ]; then
    echo -e "${RED}❌ EMAIL_TO não configurado no .env${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Preparando arquivos...${NC}"

# Criar diretório temporário
TEMP_DIR="/tmp/sofia-insights-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TEMP_DIR"

# Copiar insights gerados
if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
    cp analytics/premium-insights/latest-geo.txt "$TEMP_DIR/"
    echo -e "${GREEN}  ✅ latest-geo.txt${NC}"
fi

if [ -f "analytics/premium-insights/latest-geo.md" ]; then
    cp analytics/premium-insights/latest-geo.md "$TEMP_DIR/"
    echo -e "${GREEN}  ✅ latest-geo.md${NC}"
fi

# Exportar dados RAW do banco
echo -e "${BLUE}📊 Exportando dados RAW...${NC}"

# Ativar venv
source venv-analytics/bin/activate

# Executar export de dados
python3 - <<PYTHON_SCRIPT
import psycopg2
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# Conectar banco
conn = psycopg2.connect(
    host=os.getenv('PGHOST', 'localhost'),
    database=os.getenv('PGDATABASE', 'sofia_db'),
    user=os.getenv('PGUSER', 'sofia'),
    password=os.getenv('PGPASSWORD', '')
)

temp_dir = "$TEMP_DIR"
last_30_days = datetime.now() - timedelta(days=30)

print("📊 Exportando dados dos últimos 30 dias...")

# 1. Funding Rounds
try:
    df_funding = pd.read_sql("""
        SELECT country, sector, amount_usd, round_type, company, announced_date
        FROM sofia.funding_rounds
        WHERE announced_date >= %s
        ORDER BY amount_usd DESC
    """, conn, params=(last_30_days,))

    if not df_funding.empty:
        df_funding.to_csv(f"{temp_dir}/funding_rounds_30d.csv", index=False)
        print(f"  ✅ funding_rounds_30d.csv ({len(df_funding)} registros)")
except Exception as e:
    print(f"  ⚠️  Funding Rounds: {e}")

# 2. Startups por país
try:
    df_startups = pd.read_sql("""
        SELECT country, sector, founded_year, employees, total_funding_usd, name
        FROM sofia.startups
        WHERE founded_year >= EXTRACT(YEAR FROM %s)
        ORDER BY total_funding_usd DESC
    """, conn, params=(last_30_days,))

    if not df_startups.empty:
        df_startups.to_csv(f"{temp_dir}/startups_recent.csv", index=False)
        print(f"  ✅ startups_recent.csv ({len(df_startups)} registros)")
except Exception as e:
    print(f"  ⚠️  Startups: {e}")

# 3. Publications/Papers
try:
    df_papers = pd.read_sql("""
        SELECT title, authors, published_date, categories, url
        FROM sofia.publications
        WHERE published_date >= %s
        ORDER BY published_date DESC
    """, conn, params=(last_30_days,))

    if not df_papers.empty:
        df_papers.to_csv(f"{temp_dir}/papers_30d.csv", index=False)
        print(f"  ✅ papers_30d.csv ({len(df_papers)} registros)")
except Exception as e:
    print(f"  ⚠️  Papers: {e}")

# 4. Market Data Brasil
try:
    df_b3 = pd.read_sql("""
        SELECT ticker, company, sector, price, change_pct, volume, date
        FROM sofia.market_data_brazil
        WHERE date >= %s
        ORDER BY date DESC, change_pct DESC
    """, conn, params=(last_30_days,))

    if not df_b3.empty:
        df_b3.to_csv(f"{temp_dir}/market_b3_30d.csv", index=False)
        print(f"  ✅ market_b3_30d.csv ({len(df_b3)} registros)")
except Exception as e:
    print(f"  ⚠️  B3: {e}")

# 5. Market Data NASDAQ
try:
    df_nasdaq = pd.read_sql("""
        SELECT ticker, company, sector, price, change_pct, volume, date
        FROM sofia.market_data_nasdaq
        WHERE date >= %s
        ORDER BY date DESC, change_pct DESC
    """, conn, params=(last_30_days,))

    if not df_nasdaq.empty:
        df_nasdaq.to_csv(f"{temp_dir}/market_nasdaq_30d.csv", index=False)
        print(f"  ✅ market_nasdaq_30d.csv ({len(df_nasdaq)} registros)")
except Exception as e:
    print(f"  ⚠️  NASDAQ: {e}")

# 6. IPO Calendar
try:
    df_ipo = pd.read_sql("""
        SELECT company, ticker, exchange, expected_date, price_range,
               sector, country, status, underwriters
        FROM sofia.ipo_calendar
        WHERE expected_date >= CURRENT_DATE
        ORDER BY expected_date ASC
    """, conn)

    if not df_ipo.empty:
        df_ipo.to_csv(f"{temp_dir}/ipo_calendar.csv", index=False)
        print(f"  ✅ ipo_calendar.csv ({len(df_ipo)} registros)")
except Exception as e:
    print(f"  ⚠️  IPO Calendar: {e}")

# 7. Jobs (se existir)
try:
    df_jobs = pd.read_sql("""
        SELECT country, sector, title, company, location, posted_date, url
        FROM sofia.jobs
        WHERE posted_date >= %s
        ORDER BY posted_date DESC
    """, conn, params=(last_30_days,))

    if not df_jobs.empty:
        df_jobs.to_csv(f"{temp_dir}/jobs_30d.csv", index=False)
        print(f"  ✅ jobs_30d.csv ({len(df_jobs)} registros)")
except Exception as e:
    print(f"  ⚠️  Jobs: Tabela não existe ou vazia")

# 8. Resumo agregado por país
try:
    summary = {}

    # Funding por país
    funding_by_country = pd.read_sql("""
        SELECT country, COUNT(*) as deals, SUM(amount_usd) as total_usd
        FROM sofia.funding_rounds
        WHERE announced_date >= %s
        GROUP BY country
        ORDER BY total_usd DESC
    """, conn, params=(last_30_days,))

    # Startups por país
    startups_by_country = pd.read_sql("""
        SELECT country, COUNT(*) as count, sector
        FROM sofia.startups
        GROUP BY country, sector
        ORDER BY count DESC
    """, conn)

    summary['funding_by_country'] = funding_by_country.to_dict(orient='records')
    summary['startups_by_country'] = startups_by_country.to_dict(orient='records')

    with open(f"{temp_dir}/summary_by_country.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"  ✅ summary_by_country.json")
except Exception as e:
    print(f"  ⚠️  Summary: {e}")

conn.close()
print("✅ Export completo!")

PYTHON_SCRIPT

echo ""
echo -e "${BLUE}📧 Enviando email...${NC}"

# Criar corpo do email
EMAIL_BODY="$TEMP_DIR/email-body.html"

cat > "$EMAIL_BODY" <<EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        h1 { color: #0066cc; }
        h2 { color: #0099cc; }
        .stats { background: #f4f4f4; padding: 15px; border-radius: 5px; }
        .file-list { background: #e8f4f8; padding: 15px; border-radius: 5px; }
        code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🌍 Sofia Pulse - Premium Insights</h1>
    <p><strong>Data:</strong> $(date '+%Y-%m-%d %H:%M:%S')</p>

    <h2>📊 Dados Incluídos</h2>
    <div class="file-list">
        <ul>
            <li><strong>latest-geo.txt/md</strong> - Insights geo-localizados prontos</li>
            <li><strong>funding_rounds_30d.csv</strong> - Rodadas de investimento (30 dias)</li>
            <li><strong>startups_recent.csv</strong> - Startups recentes por país/setor</li>
            <li><strong>papers_30d.csv</strong> - Papers acadêmicos publicados</li>
            <li><strong>market_b3_30d.csv</strong> - Dados de ações B3</li>
            <li><strong>market_nasdaq_30d.csv</strong> - Dados de ações NASDAQ</li>
            <li><strong>ipo_calendar.csv</strong> - Calendário de IPOs futuros</li>
            <li><strong>jobs_30d.csv</strong> - Vagas de emprego por setor/país</li>
            <li><strong>summary_by_country.json</strong> - Resumo agregado por país</li>
        </ul>
    </div>

    <h2>🎯 Como Usar</h2>
    <ol>
        <li>Baixe os arquivos CSV anexos</li>
        <li>Use os insights em <code>latest-geo.txt</code> diretamente</li>
        <li>Ou pegue os CSVs e mande para outra IA gerar insights customizados</li>
        <li>Dados raw estão prontos para análise em Excel, Python, etc</li>
    </ol>

    <h2>🇧🇷 Foco Brasil</h2>
    <p>Os dados incluem análise detalhada do Brasil:</p>
    <ul>
        <li>Funding por setor no Brasil</li>
        <li>Startups brasileiras por área</li>
        <li>IPOs previstos na B3</li>
        <li>Papers de universidades brasileiras (USP, Unicamp, etc)</li>
        <li>Vagas de emprego no Brasil por setor tech</li>
    </ul>

    <p><em>Gerado automaticamente pelo Sofia Pulse Premium Insights v2.0</em></p>
</body>
</html>
EOF

# Compactar arquivos
cd "$TEMP_DIR"
tar -czf sofia-insights-$(date +%Y%m%d).tar.gz *.csv *.json *.txt *.md 2>/dev/null || true

# Enviar email usando Python (mais confiável que sendmail)
cd "$SCRIPT_DIR"

python3 - <<PYTHON_EMAIL
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# Configurações
email_to = os.getenv('EMAIL_TO')
email_from = os.getenv('EMAIL_FROM', email_to)
smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_user = os.getenv('SMTP_USER', email_from)
smtp_pass = os.getenv('SMTP_PASS', '')

if not smtp_pass:
    print("❌ SMTP_PASS não configurado no .env")
    print("   Para Gmail: Use 'App Password' (não a senha normal)")
    print("   https://myaccount.google.com/apppasswords")
    exit(1)

# Criar mensagem
msg = MIMEMultipart()
msg['From'] = email_from
msg['To'] = email_to
msg['Subject'] = f"📊 Sofia Pulse - Insights Geo-Localizados {os.popen('date +%Y-%m-%d').read().strip()}"

# Corpo HTML
with open('$EMAIL_BODY', 'r') as f:
    html = f.read()
msg.attach(MIMEText(html, 'html'))

# Anexar arquivos
temp_dir = Path('$TEMP_DIR')
attached_files = []

for file_path in temp_dir.glob('*'):
    if file_path.is_file() and file_path.suffix in ['.csv', '.json', '.txt', '.md', '.gz']:
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={file_path.name}')
            msg.attach(part)
            attached_files.append(file_path.name)
            print(f"  📎 {file_path.name}")

print(f"\n📧 Enviando para: {email_to}")

try:
    # Conectar e enviar
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    server.quit()

    print("✅ Email enviado com sucesso!")
    print(f"   {len(attached_files)} arquivo(s) anexado(s)")

except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")
    exit(1)

PYTHON_EMAIL

# Limpar arquivos temporários
echo ""
echo -e "${BLUE}🗑️  Limpando arquivos temporários...${NC}"
rm -rf "$TEMP_DIR"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Email enviado com sucesso!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""
