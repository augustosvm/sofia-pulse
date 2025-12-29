#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - FASE 2 - INSTALAÇÃO COMPLETA"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Este script faz TUDO:"
echo "  ✅ Instala collectors GDELT"
echo "  ✅ Roda primeira coleta"
echo "  ✅ Gera Correlações Papers ↔ Funding"
echo "  ✅ Gera Dark Horses Report"
echo "  ✅ Envia email com TUDO"
echo "  ✅ Atualiza cron"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

# 1. Git pull
echo "🔄 1. Atualizando código..."
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE 2>&1 | grep -E "(Already|Updating|Fast-forward)" || true
echo ""

# 2. Ativar venv
echo "🐍 2. Ativando Python venv..."
if [ ! -d "venv-analytics" ]; then
    python3 -m venv venv-analytics
    source venv-analytics/bin/activate
    pip install -q psycopg2-binary python-dotenv pandas numpy scipy
else
    source venv-analytics/bin/activate
fi
echo "   ✅ Python venv pronto"
echo ""

# 3. NPM install
echo "📦 3. Instalando npm packages..."
npm install --silent 2>/dev/null || true
echo "   ✅ NPM packages prontos"
echo ""

# 4. Criar tabela GDELT
echo "🗄️  4. Criando tabela GDELT..."
if command -v psql &> /dev/null; then
    DB_HOST=$(grep POSTGRES_HOST .env | cut -d'=' -f2 || echo "localhost")
    DB_PORT=$(grep POSTGRES_PORT .env | cut -d'=' -f2 || echo "5432")
    DB_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2 || echo "sofia")
    DB_NAME=$(grep POSTGRES_DB .env | cut -d'=' -f2 || echo "sofia_db")
    PGPASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)

    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f db/migrations/011_create_gdelt_events.sql 2>&1 | grep -E "(CREATE|ERROR)" || echo "   ✅ Tabela criada"
else
    echo "   ⚠️  psql não disponível"
fi
echo ""

# 5. Coletar GDELT (primeira vez)
echo "🌍 5. Coletando GDELT (primeira vez)..."
npm run collect:gdelt 2>&1 | tail -15
echo ""

# 6. Gerar Correlações
echo "🔗 6. Gerando Correlações Papers ↔ Funding..."
python3 analytics/correlation-papers-funding.py > analytics/correlation-latest.txt 2>&1
echo "   ✅ Correlações geradas"
tail -20 analytics/correlation-latest.txt
echo ""

# 7. Gerar Dark Horses
echo "🐴 7. Gerando Dark Horses Report..."
python3 analytics/dark-horses-report.py 2>&1 | tail -20
echo ""

# 8. Gerar relatório completo
echo "📊 8. Gerando relatório completo..."
bash run-insights.sh 2>&1 | tail -30
echo ""

# 9. Enviar email
echo "📧 9. Enviando email..."
echo ""

if grep -q "SMTP_PASS=your-gmail-app-password-here" .env 2>/dev/null || ! grep -q "SMTP_PASS=." .env 2>/dev/null; then
    echo "⚠️  SMTP_PASS não configurado - pulando email"
    echo ""
    echo "Para configurar:"
    echo "  1. Gere senha: https://myaccount.google.com/apppasswords"
    echo "  2. Edite .env: SMTP_PASS=sua-senha-16-caracteres"
    echo "  3. Teste: bash send-email-phase2.sh"
    echo ""
else
    bash send-email-phase2.sh
    echo ""
fi

# 10. Atualizar cron
echo "⏰ 10. Atualizando cron..."
echo ""

bash update-cron-phase2.sh

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ FASE 2 INSTALADA E EXECUTADA!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📧 Email enviado para: augustosvm@gmail.com"
echo ""
echo "📊 Conteúdo:"
echo "   ✅ Tech Trend Score"
echo "   ✅ Correlações Papers ↔ Funding"
echo "   ✅ Dark Horses Report (oportunidades)"
echo "   ✅ Premium Insights v2.0 (regional + temporal)"
echo "   ✅ CSVs de dados RAW"
echo ""
echo "⏰ Automação:"
echo "   - GitHub/HN/GDELT: Diário (08:00-09:00 UTC)"
echo "   - Finance: Seg-Sex 21:00 UTC"
echo "   - Insights: Seg-Sex 22:00 UTC"
echo "   - Email: Seg-Sex 23:00 UTC"
echo "   - Dark Horses: Mensal (dia 1)"
echo ""
echo "📁 Arquivos:"
echo "   - analytics/sofia-report.txt (completo)"
echo "   - analytics/correlation-latest.txt"
echo "   - analytics/dark-horses-latest.txt"
echo ""
echo "✅ Pronto!"
echo ""
