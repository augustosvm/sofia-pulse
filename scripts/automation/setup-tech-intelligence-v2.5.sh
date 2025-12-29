#!/bin/bash
set -e

echo "============================================================================"
echo "🚀 SOFIA PULSE - Tech Intelligence v2.5 - Setup Completo"
echo "============================================================================"
echo ""
echo "Este script faz TUDO automaticamente:"
echo "  ✅ Instala collectors (GitHub Trending + HackerNews)"
echo "  ✅ Roda primeira coleta (teste)"
echo "  ✅ Gera insights REGIONAIS e TEMPORAIS"
echo "  ✅ Configura email automático"
echo "  ✅ Adiciona ao cron (automação 24/7)"
echo ""
echo "============================================================================"
echo ""

# Detectar diretório
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
else
    SOFIA_DIR="$(pwd)"
fi

cd "$SOFIA_DIR"

echo "📁 Diretório: $SOFIA_DIR"
echo ""

# ============================================================================
# 1. GIT PULL (atualizar código)
# ============================================================================

echo "🔄 1. Atualizando código..."
echo ""

if [ -d ".git" ]; then
    # Fazer stash se houver mudanças locais
    if ! git diff-index --quiet HEAD --; then
        echo "   ⚠️  Mudanças locais detectadas, fazendo stash..."
        git stash
    fi

    git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE || {
        echo "   ⚠️  Pull falhou, continuando com código local..."
    }
fi

echo "   ✅ Código atualizado"
echo ""

# ============================================================================
# 2. VERIFICAR DEPENDÊNCIAS
# ============================================================================

echo "🔍 2. Verificando dependências..."
echo ""

# Node.js
if ! command -v node &> /dev/null; then
    echo "   ❌ Node.js não encontrado!"
    echo "   Instale: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs"
    exit 1
fi
echo "   ✅ Node.js $(node --version)"

# npm
if ! command -v npm &> /dev/null; then
    echo "   ❌ npm não encontrado!"
    exit 1
fi
echo "   ✅ npm $(npm --version)"

# PostgreSQL client
if ! command -v psql &> /dev/null; then
    echo "   ⚠️  PostgreSQL client não encontrado (opcional para testes SQL)"
fi

# Python3
if ! command -v python3 &> /dev/null; then
    echo "   ❌ Python3 não encontrado!"
    exit 1
fi
echo "   ✅ Python3 $(python3 --version)"

# NPM packages
echo "   📦 Instalando/atualizando pacotes npm..."
npm install --silent

echo ""

# ============================================================================
# 3. CRIAR/ATIVAR VIRTUAL ENVIRONMENT PYTHON
# ============================================================================

echo "🐍 3. Configurando Python virtual environment..."
echo ""

if [ ! -d "venv-analytics" ]; then
    echo "   📦 Criando venv-analytics..."
    python3 -m venv venv-analytics
fi

source venv-analytics/bin/activate

# Instalar dependências Python
echo "   📦 Instalando dependências Python..."
pip install --quiet --upgrade pip
pip install --quiet psycopg2-binary python-dotenv pandas numpy scipy scikit-learn

echo "   ✅ Python environment pronto"
echo ""

# ============================================================================
# 4. VERIFICAR .ENV (configuração de email)
# ============================================================================

echo "📧 4. Verificando configuração de email..."
echo ""

if [ ! -f ".env" ]; then
    echo "   ⚠️  Arquivo .env não encontrado, criando..."
    cat > .env << 'ENVEOF'
# Database (PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=your-password-here
POSTGRES_DB=sofia_db

# Email (Gmail SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=augustosvm@gmail.com
SMTP_PASS=your-gmail-app-password-here
EMAIL_TO=augustosvm@gmail.com

# APIs (opcional)
GITHUB_TOKEN=
ALPHA_VANTAGE_API_KEY=

# Gemini AI (opcional - para narrativas)
GEMINI_API_KEY=
ENVEOF
fi

# Verificar se SMTP_PASS está configurado
if grep -q "SMTP_PASS=your-gmail-app-password-here" .env 2>/dev/null || ! grep -q "SMTP_PASS=." .env 2>/dev/null; then
    echo "   ⚠️  SMTP_PASS não configurado no .env"
    echo "   📧 Email: augustosvm@gmail.com já configurado"
    echo ""
    echo "   Para habilitar email automático:"
    echo "   1. Vá em: https://myaccount.google.com/apppasswords"
    echo "   2. Gere uma senha de app (16 caracteres)"
    echo "   3. Adicione no .env: SMTP_PASS=xxxx-xxxx-xxxx-xxxx"
    echo ""
else
    echo "   ✅ Email configurado: augustosvm@gmail.com"
fi

echo ""

# ============================================================================
# 5. CRIAR DIRETÓRIOS
# ============================================================================

echo "📁 5. Criando diretórios necessários..."
echo ""

mkdir -p logs
mkdir -p analytics/premium-insights
mkdir -p analytics/tech-trends
mkdir -p data/exports

# Criar logs se não existirem
if [ -w /var/log ]; then
    sudo touch /var/log/sofia-{github,hn,trends,finance,arxiv,openalex,ai-companies,patents,hkex,nih,unis,cardboard,ipo,jobs,insights-v2,email,backup}.log 2>/dev/null || true
    sudo chown $USER:$USER /var/log/sofia-*.log 2>/dev/null || true
fi

echo "   ✅ Diretórios criados"
echo ""

# ============================================================================
# 6. RODAR MIGRATIONS (criar tabelas)
# ============================================================================

echo "🗄️  6. Rodando migrations (criar tabelas)..."
echo ""

# Verificar se PostgreSQL está acessível
DB_HOST=$(grep POSTGRES_HOST .env | cut -d'=' -f2)
DB_PORT=$(grep POSTGRES_PORT .env | cut -d'=' -f2)
DB_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
DB_NAME=$(grep POSTGRES_DB .env | cut -d'=' -f2)

if command -v psql &> /dev/null; then
    echo "   📊 Criando tabelas github_trending e hackernews_stories..."

    # Tentar rodar migrations
    PGPASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2) psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f db/migrations/009_create_github_trending.sql 2>/dev/null && echo "      ✅ github_trending criada" || echo "      ⚠️  github_trending já existe ou erro de conexão"

    PGPASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2) psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f db/migrations/010_create_hackernews_stories.sql 2>/dev/null && echo "      ✅ hackernews_stories criada" || echo "      ⚠️  hackernews_stories já existe ou erro de conexão"
else
    echo "   ⚠️  psql não disponível, migrations serão executadas pelos collectors"
fi

echo ""

# ============================================================================
# 7. PRIMEIRA COLETA (TESTE)
# ============================================================================

echo "🔥 7. Executando PRIMEIRA COLETA (teste)..."
echo ""
echo "   Isso vai coletar dados REAIS do GitHub e HackerNews"
echo "   (Pode levar 1-2 minutos devido a rate limits)"
echo ""

# GitHub Trending
echo "   📊 [1/2] Coletando GitHub Trending..."
npm run collect:github-trending 2>&1 | tail -20 || {
    echo "      ⚠️  Erro ao coletar GitHub (pode ser rate limit ou DB offline)"
    echo "      Continuando..."
}
echo ""

# HackerNews
echo "   📰 [2/2] Coletando HackerNews..."
npm run collect:hackernews 2>&1 | tail -20 || {
    echo "      ⚠️  Erro ao coletar HackerNews"
    echo "      Continuando..."
}
echo ""

echo "   ✅ Primeira coleta concluída"
echo ""

# ============================================================================
# 8. GERAR TECH TREND SCORE (primeira vez)
# ============================================================================

echo "🧮 8. Gerando Tech Trend Score..."
echo ""

if command -v psql &> /dev/null && PGPASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2) psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM sofia.github_trending" &>/dev/null; then
    echo "   Calculando scores..."
    python3 analytics/tech-trend-score-simple.py > analytics/tech-trends/latest-scores.txt 2>&1 || {
        echo "      ⚠️  Erro ao calcular scores (pode ser falta de dados)"
    }

    if [ -f "analytics/tech-trends/latest-scores.txt" ]; then
        echo ""
        echo "   📊 Preview dos Top 10:"
        echo ""
        grep -A 15 "TOP 20 TECNOLOGIAS" analytics/tech-trends/latest-scores.txt | head -20 || true
        echo ""
    fi
else
    echo "   ⚠️  Banco offline ou sem dados ainda"
    echo "   Scores serão gerados quando houver dados"
fi

echo ""

# ============================================================================
# 9. CRIAR SCRIPT DE INSIGHTS INTEGRADO
# ============================================================================

echo "📊 9. Criando script de insights REGIONAL + TEMPORAL + TECH TRENDS..."
echo ""

cat > generate-insights-complete.sh << 'INSIGHTS_EOF'
#!/bin/bash
set -e

echo "============================================================================"
echo "🤖 SOFIA PULSE - Insights Completos (Regional + Temporal + Tech Trends)"
echo "============================================================================"
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"

cd "$SOFIA_DIR"

# Ativar venv Python
source venv-analytics/bin/activate

# Criar diretórios
mkdir -p analytics/premium-insights
mkdir -p analytics/tech-trends
mkdir -p data/exports

echo "📊 1. Gerando Premium Insights v2.0 (Regional + Temporal)..."
echo ""

if [ -f "generate-insights-v2.0.sh" ]; then
    bash generate-insights-v2.0.sh
else
    echo "   ⚠️  generate-insights-v2.0.sh não encontrado"
fi

echo ""
echo "🔥 2. Gerando Tech Trend Score..."
echo ""

python3 analytics/tech-trend-score-simple.py > analytics/tech-trends/latest-scores.txt 2>&1 || {
    echo "   ⚠️  Erro ao gerar Tech Trend Score"
}

echo ""
echo "📄 3. Consolidando insights em um único arquivo..."
echo ""

# Consolidar tudo
cat > analytics/premium-insights/latest-complete.txt << 'COMPLETE_EOF'
════════════════════════════════════════════════════════════════════════════════
                    🤖 SOFIA PULSE - INTELLIGENCE REPORT
════════════════════════════════════════════════════════════════════════════════

📅 Generated: $(date '+%Y-%m-%d %H:%M:%S UTC')
📧 Recipient: augustosvm@gmail.com

════════════════════════════════════════════════════════════════════════════════
                        PARTE 1: TECH TREND SCORE
════════════════════════════════════════════════════════════════════════════════

COMPLETE_EOF

# Adicionar Tech Trends
if [ -f "analytics/tech-trends/latest-scores.txt" ]; then
    cat analytics/tech-trends/latest-scores.txt >> analytics/premium-insights/latest-complete.txt
else
    echo "(Sem dados de Tech Trends ainda)" >> analytics/premium-insights/latest-complete.txt
fi

cat >> analytics/premium-insights/latest-complete.txt << 'COMPLETE_EOF2'

════════════════════════════════════════════════════════════════════════════════
                 PARTE 2: INSIGHTS REGIONAIS E TEMPORAIS
════════════════════════════════════════════════════════════════════════════════

COMPLETE_EOF2

# Adicionar Premium Insights v2.0
if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
    tail -n +5 analytics/premium-insights/latest-geo.txt >> analytics/premium-insights/latest-complete.txt
else
    echo "(Sem dados de Premium Insights ainda)" >> analytics/premium-insights/latest-complete.txt
fi

echo ""
echo "✅ Insights consolidados em: analytics/premium-insights/latest-complete.txt"
echo ""
echo "📊 Preview:"
echo ""
head -80 analytics/premium-insights/latest-complete.txt
echo ""
echo "..."
echo ""
echo "✅ Geração completa!"
INSIGHTS_EOF

chmod +x generate-insights-complete.sh

echo "   ✅ Script criado: generate-insights-complete.sh"
echo ""

# ============================================================================
# 10. ATUALIZAR SCRIPT DE EMAIL
# ============================================================================

echo "📧 10. Atualizando script de email..."
echo ""

cat > send-insights-email-complete.sh << 'EMAIL_EOF'
#!/bin/bash
set -e

echo "============================================================================"
echo "📧 SOFIA PULSE - Envio de Email com Insights Completos"
echo "============================================================================"
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"

cd "$SOFIA_DIR"

# Carregar .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Verificar se SMTP está configurado
if [ -z "$SMTP_PASS" ] || [ "$SMTP_PASS" = "your-gmail-app-password-here" ]; then
    echo "❌ SMTP_PASS não configurado no .env"
    echo "   Configure em: .env"
    echo "   Gere senha em: https://myaccount.google.com/apppasswords"
    exit 1
fi

EMAIL_TO="${EMAIL_TO:-augustosvm@gmail.com}"
SMTP_USER="${SMTP_USER:-augustosvm@gmail.com}"

echo "📧 Enviando para: $EMAIL_TO"
echo ""

# Verificar se insights existem
if [ ! -f "analytics/premium-insights/latest-complete.txt" ]; then
    echo "❌ Insights não encontrados!"
    echo "   Execute: bash generate-insights-complete.sh"
    exit 1
fi

# Exportar dados RAW para anexar
echo "📊 Exportando dados RAW..."
echo ""

mkdir -p data/exports

# Exportar CSVs (se banco estiver disponível)
if command -v psql &> /dev/null; then
    DB_HOST="${POSTGRES_HOST:-localhost}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    DB_USER="${POSTGRES_USER:-sofia}"
    DB_NAME="${POSTGRES_DB:-sofia_db}"

    # GitHub Trending
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT language, COUNT(*) as repos, SUM(stars) as total_stars FROM sofia.github_trending WHERE language IS NOT NULL GROUP BY language ORDER BY total_stars DESC LIMIT 50) TO 'data/exports/github_trending.csv' CSV HEADER" 2>/dev/null || true

    # HackerNews
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT unnest(mentioned_technologies) as tech, COUNT(*) as mentions FROM sofia.hackernews_stories GROUP BY tech ORDER BY mentions DESC LIMIT 50) TO 'data/exports/hackernews_tech.csv' CSV HEADER" 2>/dev/null || true

    # Funding (últimos 30 dias)
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\COPY (SELECT * FROM sofia.funding_rounds WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days' ORDER BY announced_date DESC) TO 'data/exports/funding_30d.csv' CSV HEADER" 2>/dev/null || true

    echo "   ✅ CSVs exportados"
else
    echo "   ⚠️  psql não disponível, CSVs não exportados"
fi

echo ""

# Enviar email via Python (mais confiável que sendemail)
cat > /tmp/send_sofia_email.py << 'PYEOF'
#!/usr/bin/env python3
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import glob

# Configuração
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
EMAIL_TO = os.getenv('EMAIL_TO')

# Criar mensagem
msg = MIMEMultipart()
msg['From'] = SMTP_USER
msg['To'] = EMAIL_TO
msg['Subject'] = f"Sofia Pulse Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"

# Corpo do email
with open('analytics/premium-insights/latest-complete.txt', 'r') as f:
    body = f.read()

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar insights TXT
with open('analytics/premium-insights/latest-complete.txt', 'rb') as f:
    attachment = MIMEApplication(f.read(), _subtype='txt')
    attachment.add_header('Content-Disposition', 'attachment', filename='sofia-insights-complete.txt')
    msg.attach(attachment)

# Anexar CSVs
csv_files = glob.glob('data/exports/*.csv')
for csv_file in csv_files:
    try:
        with open(csv_file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='csv')
            filename = os.path.basename(csv_file)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
    except:
        pass

# Enviar
print(f"📧 Enviando email para {EMAIL_TO}...")
try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()
    print("✅ Email enviado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")
    exit(1)
PYEOF

python3 /tmp/send_sofia_email.py

echo ""
echo "✅ Email enviado!"
echo ""
echo "📧 Conteúdo enviado:"
echo "   - Insights completos (TXT)"
echo "   - Tech Trend Score"
echo "   - Premium Insights v2.0"
echo "   - CSVs de dados RAW"
echo ""
EMAIL_EOF

chmod +x send-insights-email-complete.sh

echo "   ✅ Script criado: send-insights-email-complete.sh"
echo ""

# ============================================================================
# 11. TESTAR GERAÇÃO DE INSIGHTS
# ============================================================================

echo "🧪 11. Testando geração de insights completos..."
echo ""

bash generate-insights-complete.sh || {
    echo "   ⚠️  Erro ao gerar insights (pode ser falta de dados)"
}

echo ""

# ============================================================================
# 12. ADICIONAR AO CRON
# ============================================================================

echo "⏰ 12. Configurando automação (cron)..."
echo ""

# Backup do cron atual
BACKUP_FILE="$HOME/crontab-backup-tech-intelligence-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No previous crontab" > "$BACKUP_FILE"

echo "   📦 Backup do cron atual: $BACKUP_FILE"
echo ""

# Criar novo cron com Tech Intelligence
cat > /tmp/sofia-crontab-tech-intelligence.txt << CRONEOF
# ============================================================================
# SOFIA PULSE - Cron Jobs com TECH INTELLIGENCE v2.5
# ============================================================================
# Gerado automaticamente em: $(date)
# Branch: claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ============================================================================
# TECH INTELLIGENCE (NOVO!)
# ============================================================================

# GitHub Trending - Diário às 08:00 UTC
0 8 * * * cd $SOFIA_DIR && npm run collect:github-trending >> /var/log/sofia-github.log 2>&1

# HackerNews - Diário às 08:30 UTC
30 8 * * * cd $SOFIA_DIR && npm run collect:hackernews >> /var/log/sofia-hn.log 2>&1

# ============================================================================
# FINANCE & RESEARCH (EXISTENTE)
# ============================================================================

# Finance (B3, NASDAQ, Funding) - Seg-Sex às 21:00 UTC
0 21 * * 1-5 cd $SOFIA_DIR && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1

# ArXiv AI Papers - Diário às 20:00 UTC
0 20 * * * cd $SOFIA_DIR && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1

# OpenAlex Papers - Diário às 20:05 UTC
5 20 * * * cd $SOFIA_DIR && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1

# AI Companies - Diário às 20:10 UTC
10 20 * * * cd $SOFIA_DIR && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1

# Patentes (WIPO China, EPO) - Diário às 01:00 UTC
0 1 * * * cd $SOFIA_DIR && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1

# IPOs Hong Kong - Seg-Sex às 02:00 UTC
0 2 * * 1-5 cd $SOFIA_DIR && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1

# NIH Grants - Semanal (segunda às 03:00 UTC)
0 3 * * 1 cd $SOFIA_DIR && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1

# Universidades Ásia - Mensal (dia 1 às 04:00 UTC)
0 4 1 * * cd $SOFIA_DIR && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1

# Cardboard Production - Semanal (segunda às 05:00 UTC)
0 5 * * 1 cd $SOFIA_DIR && npm run collect:cardboard >> /var/log/sofia-cardboard.log 2>&1

# IPO Calendar - Diário às 06:00 UTC
0 6 * * * cd $SOFIA_DIR && npm run collect:ipo-calendar >> /var/log/sofia-ipo.log 2>&1

# Jobs - Diário às 07:00 UTC
0 7 * * * cd $SOFIA_DIR && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# ============================================================================
# INSIGHTS GENERATION (ATUALIZADO - COMPLETO!)
# ============================================================================

# Insights Completos (Regional + Temporal + Tech Trends) - Seg-Sex às 22:00 UTC
0 22 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && ./generate-insights-complete.sh >> /var/log/sofia-insights-complete.log 2>&1

# ============================================================================
# EMAIL & REPORTING (ATUALIZADO!)
# ============================================================================

# Email com Insights Completos - Seg-Sex às 23:00 UTC
0 23 * * 1-5 cd $SOFIA_DIR && ./send-insights-email-complete.sh >> /var/log/sofia-email.log 2>&1

# ============================================================================
# BACKUPS (mantidos do cron original)
# ============================================================================

# Auto-recovery
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh 2>/dev/null || true

# Backups diversos
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh 2>/dev/null || true
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh 2>/dev/null || true
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh 2>/dev/null || true

# Sofia backup
0 4 * * * cd $SOFIA_DIR && ./scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1 || true

# ============================================================================
# TOTAL: 16 collectors + 2 insights/email + 5 backups = 23 jobs
# ============================================================================
CRONEOF

# Substituir $SOFIA_DIR pela variável real
sed -i "s|\$SOFIA_DIR|$SOFIA_DIR|g" /tmp/sofia-crontab-tech-intelligence.txt

# Mostrar diff
echo "   📊 Comparação com cron atual:"
echo ""
diff -u "$BACKUP_FILE" /tmp/sofia-crontab-tech-intelligence.txt || true
echo ""

# Perguntar confirmação
read -p "   Instalar novo crontab com Tech Intelligence? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    crontab /tmp/sofia-crontab-tech-intelligence.txt
    echo "   ✅ Crontab instalado!"
else
    echo "   ⏭️  Instalação do cron pulada"
    echo "   Para instalar manualmente: crontab /tmp/sofia-crontab-tech-intelligence.txt"
fi

echo ""

# ============================================================================
# 13. RESUMO FINAL
# ============================================================================

echo "============================================================================"
echo "✅ SETUP COMPLETO!"
echo "============================================================================"
echo ""
echo "📊 O que foi instalado:"
echo ""
echo "   ✅ Collectors:"
echo "      - GitHub Trending (diário 08:00 UTC)"
echo "      - HackerNews (diário 08:30 UTC)"
echo "      - 12 collectors existentes (finance, research, patents, etc)"
echo ""
echo "   ✅ Analytics:"
echo "      - Tech Trend Score (ranking de tecnologias)"
echo "      - Premium Insights v2.0 (regional + temporal)"
echo "      - Insights Completos (tudo em um arquivo)"
echo ""
echo "   ✅ Automação:"
echo "      - Coleta diária automática"
echo "      - Insights gerados às 22:00 UTC (seg-sex)"
echo "      - Email enviado às 23:00 UTC (seg-sex)"
echo "      - Email: augustosvm@gmail.com"
echo ""
echo "============================================================================"
echo ""
echo "🚀 PRÓXIMOS PASSOS:"
echo ""
echo "1. Verificar se dados foram coletados:"
echo "   cat analytics/tech-trends/latest-scores.txt"
echo ""
echo "2. Ver insights completos:"
echo "   cat analytics/premium-insights/latest-complete.txt"
echo ""
echo "3. Testar envio de email (se SMTP configurado):"
echo "   bash send-insights-email-complete.sh"
echo ""
echo "4. Verificar cron instalado:"
echo "   crontab -l"
echo ""
echo "5. Acompanhar logs em tempo real:"
echo "   tail -f /var/log/sofia-*.log"
echo ""
echo "============================================================================"
echo ""
echo "📧 CONFIGURAÇÃO DE EMAIL:"
echo ""

if grep -q "SMTP_PASS=your-gmail-app-password-here" .env 2>/dev/null || ! grep -q "SMTP_PASS=." .env 2>/dev/null; then
    echo "   ⚠️  Email NÃO configurado ainda"
    echo ""
    echo "   Para receber insights no email:"
    echo "   1. Acesse: https://myaccount.google.com/apppasswords"
    echo "   2. Gere uma senha de app (16 caracteres)"
    echo "   3. Edite .env e adicione: SMTP_PASS=xxxx-xxxx-xxxx-xxxx"
    echo "   4. Teste: bash send-insights-email-complete.sh"
else
    echo "   ✅ Email configurado e pronto!"
    echo "   📧 Destinatário: augustosvm@gmail.com"
    echo ""
    echo "   Você receberá emails com:"
    echo "   - Tech Trend Score (Top 20 tecnologias)"
    echo "   - Premium Insights v2.0 (regional + temporal)"
    echo "   - CSVs de dados RAW"
    echo ""
    echo "   Horário: Seg-Sex às 23:00 UTC (20:00 BRT)"
fi

echo ""
echo "============================================================================"
echo ""
echo "💡 INSIGHTS DISPONÍVEIS:"
echo ""
echo "   📊 Tech Trend Score:"
echo "      - Top 20 tecnologias emergentes"
echo "      - Dark Horses (alto GitHub, baixo funding)"
echo "      - Hype Check (alto HN, baixo GitHub)"
echo "      - Por linguagem, por framework"
echo ""
echo "   🌍 Premium Insights v2.0:"
echo "      - Análise geográfica (por país/continente)"
echo "      - Análise temporal (crescimento, anomalias)"
echo "      - Especialização regional"
echo "      - IPOs futuros"
echo "      - Oceano Vermelho vs Azul"
echo ""
echo "============================================================================"
echo ""
echo "✅ Setup concluído com sucesso!"
echo ""
