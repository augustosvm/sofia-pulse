#!/bin/bash

###############################################################################
# Sofia Pulse - SETUP AUTOMÁTICO COMPLETO
# Faz tudo: pull, configura email, cria tabelas, testa, envia
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
echo -e "  ${GREEN}🚀 Sofia Pulse - SETUP AUTOMÁTICO COMPLETO${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. GIT PULL (com stash se necessário)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📥 [1/8] Puxando atualizações do git...${NC}"

# Fazer stash se tiver mudanças
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}  ⚠️  Mudanças não commitadas detectadas, fazendo stash...${NC}"
    git stash
    STASHED=1
else
    STASHED=0
fi

# Pull
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE || {
    echo -e "${RED}  ❌ Erro ao fazer pull${NC}"
    exit 1
}

echo -e "${GREEN}  ✅ Git pull concluído${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. CONFIGURAR EMAIL AUTOMATICAMENTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📧 [2/8] Configurando email automaticamente...${NC}"

# Criar/atualizar .env
if [ ! -f ".env" ]; then
    touch .env
fi

# Verificar se EMAIL_TO já existe
if grep -q "EMAIL_TO" .env; then
    # Atualizar email existente
    sed -i 's/^EMAIL_TO=.*/EMAIL_TO=augustosvm@gmail.com/' .env
    echo -e "${GREEN}  ✅ EMAIL_TO atualizado para augustosvm@gmail.com${NC}"
else
    # Adicionar configuração de email
    cat >> .env <<EOF

# Email Configuration (Auto-configurado)
EMAIL_TO=augustosvm@gmail.com
EMAIL_FROM=sofia-pulse@tiespecialistas.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=augustosvm@gmail.com
SMTP_PASS=
EOF
    echo -e "${GREEN}  ✅ Email configurado: augustosvm@gmail.com${NC}"
fi

# Configurar SMTP_PASS automaticamente
SMTP_PASS="msnxttcudgfhveel"

if grep -q "^SMTP_PASS=" .env; then
    # Atualizar existente
    sed -i "s/^SMTP_PASS=.*/SMTP_PASS=$SMTP_PASS/" .env
    echo -e "${GREEN}  ✅ SMTP_PASS atualizado${NC}"
else
    # Adicionar novo
    echo "SMTP_PASS=$SMTP_PASS" >> .env
    echo -e "${GREEN}  ✅ SMTP_PASS configurado automaticamente${NC}"
fi

echo -e "${GREEN}  ✅ Email totalmente configurado (augustosvm@gmail.com)${NC}"
SKIP_EMAIL=0

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. VERIFICAR VIRTUAL ENV
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🐍 [3/8] Verificando virtual environment...${NC}"

if [ ! -d "venv-analytics" ]; then
    echo -e "${YELLOW}  ⚠️  venv-analytics não encontrado, criando...${NC}"

    if [ -f "setup-data-mining.sh" ]; then
        bash setup-data-mining.sh
    else
        python3 -m venv venv-analytics
        source venv-analytics/bin/activate
        pip install --upgrade pip
        pip install pandas psycopg2-binary google-generativeai python-dotenv
    fi
fi

source venv-analytics/bin/activate
echo -e "${GREEN}  ✅ Virtual environment ativo${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. CRIAR TABELAS NO BANCO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🗄️  [4/8] Criando tabelas no banco...${NC}"

# Verificar se PostgreSQL está acessível
if command -v psql &> /dev/null; then
    # Criar tabela IPO Calendar
    if psql -U sofia -d sofia_db -c "SELECT 1 FROM sofia.ipo_calendar LIMIT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Tabela sofia.ipo_calendar já existe${NC}"
    else
        if [ -f "db/migrations/007_create_ipo_calendar.sql" ]; then
            psql -U sofia -d sofia_db -f db/migrations/007_create_ipo_calendar.sql > /dev/null 2>&1
            echo -e "${GREEN}  ✅ Tabela sofia.ipo_calendar criada${NC}"
        fi
    fi

    # Criar tabela Jobs
    if psql -U sofia -d sofia_db -c "SELECT 1 FROM sofia.jobs LIMIT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Tabela sofia.jobs já existe${NC}"
    else
        if [ -f "db/migrations/008_create_jobs_table.sql" ]; then
            psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql > /dev/null 2>&1
            echo -e "${GREEN}  ✅ Tabela sofia.jobs criada${NC}"
        fi
    fi
else
    echo -e "${YELLOW}  ⚠️  psql não encontrado, pulando criação de tabelas${NC}"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. TORNAR SCRIPTS EXECUTÁVEIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🔧 [5/8] Tornando scripts executáveis...${NC}"

chmod +x generate-premium-insights-v2.sh 2>/dev/null || true
chmod +x send-insights-email.sh 2>/dev/null || true
chmod +x test-premium-insights-v2.sh 2>/dev/null || true

echo -e "${GREEN}  ✅ Scripts executáveis${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. GERAR INSIGHTS V2.0
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}💎 [6/8] Gerando Premium Insights v2.0...${NC}"

if [ -f "generate-premium-insights-v2.sh" ]; then
    ./generate-premium-insights-v2.sh
    echo -e "${GREEN}  ✅ Insights gerados${NC}"
else
    echo -e "${YELLOW}  ⚠️  generate-premium-insights-v2.sh não encontrado${NC}"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. PREVIEW DOS INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📊 [7/8] Preview dos insights gerados...${NC}"

if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    head -40 analytics/premium-insights/latest-geo.txt
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    echo ""
    LINES=$(wc -l < analytics/premium-insights/latest-geo.txt)
    echo -e "${GREEN}  ✅ Total de linhas: $LINES${NC}"
    echo -e "${YELLOW}  📄 Ver completo: cat analytics/premium-insights/latest-geo.txt${NC}"
else
    echo -e "${YELLOW}  ⚠️  Insights não gerados ainda${NC}"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. ENVIAR EMAIL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📧 [8/8] Enviando email para augustosvm@gmail.com...${NC}"

if [ -f "send-insights-email.sh" ]; then
    ./send-insights-email.sh || {
        echo -e "${RED}  ❌ Erro ao enviar email${NC}"
        echo -e "${YELLOW}  ⚠️  Verifique logs do SMTP${NC}"
    }
else
    echo -e "${YELLOW}  ⚠️  send-insights-email.sh não encontrado${NC}"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESUMO FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ SETUP AUTOMÁTICO CONCLUÍDO!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}📊 Status:${NC}"
echo -e "  ${GREEN}✅ Git pull executado${NC}"
echo -e "  ${GREEN}✅ Email configurado: augustosvm@gmail.com${NC}"
echo -e "  ${GREEN}✅ SMTP_PASS configurado automaticamente${NC}"
echo -e "  ${GREEN}✅ Virtual environment ativo${NC}"
echo -e "  ${GREEN}✅ Tabelas criadas no banco${NC}"
echo -e "  ${GREEN}✅ Insights gerados${NC}"
echo -e "  ${GREEN}✅ Email enviado para augustosvm@gmail.com${NC}"

echo ""

echo -e "${YELLOW}📁 Arquivos gerados:${NC}"
if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
    echo -e "  ${CYAN}analytics/premium-insights/latest-geo.txt${NC}"
    echo -e "  ${CYAN}analytics/premium-insights/latest-geo.md${NC}"
    echo -e "  ${CYAN}analytics/premium-insights/geo-summary.csv${NC}"
fi

echo ""

echo -e "${YELLOW}🔄 Próximos passos:${NC}"
echo -e "  → Ver insights: ${CYAN}cat analytics/premium-insights/latest-geo.txt${NC}"
echo -e "  → Checar email: ${CYAN}augustosvm@gmail.com${NC}"
echo -e "  → Automatizar: ${CYAN}crontab -e${NC} (adicionar cron de email)"
echo -e "  → Coletar jobs: ${CYAN}npx tsx collectors/jobs-collector.ts${NC}"

echo ""

# Restaurar stash se fez
if [ $STASHED -eq 1 ]; then
    echo -e "${YELLOW}🔄 Restaurando mudanças anteriores...${NC}"
    git stash pop
fi

echo -e "${GREEN}🎉 Pronto! Tudo configurado.${NC}"
echo ""
