#!/bin/bash

###############################################################################
# Sofia Pulse - Setup Completo de Email + Jobs
# Configura email automático e collector de vagas
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
echo -e "  ${GREEN}📧 Sofia Pulse - Setup Email + Jobs${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. VERIFICAR SE ARQUIVOS EXISTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📁 [1/5] Verificando arquivos...${NC}"

FILES=(
    "send-insights-email.sh"
    "collectors/jobs-collector.ts"
    "db/migrations/008_create_jobs_table.sql"
    "data/brazilian-universities.json"
)

MISSING=0

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ $file NÃO ENCONTRADO${NC}"
        MISSING=1
    fi
done

echo ""

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}❌ Faltam arquivos necessários. Execute git pull primeiro.${NC}"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. CONFIGURAR .ENV (EMAIL)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}⚙️  [2/5] Configurando .env para email...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}  ⚠️  Arquivo .env não encontrado, criando...${NC}"
    touch .env
fi

# Verificar se EMAIL_TO já existe
if grep -q "EMAIL_TO" .env; then
    echo -e "${GREEN}  ✅ EMAIL_TO já configurado${NC}"
else
    echo -e "${YELLOW}  📧 Digite seu email para receber insights:${NC}"
    read -r -p "  Email: " USER_EMAIL

    if [ -z "$USER_EMAIL" ]; then
        echo -e "${RED}  ❌ Email não pode ser vazio${NC}"
        exit 1
    fi

    echo "" >> .env
    echo "# Email Configuration" >> .env
    echo "EMAIL_TO=$USER_EMAIL" >> .env
    echo "EMAIL_FROM=sofia-pulse@seu-dominio.com" >> .env
    echo "" >> .env
    echo "# SMTP (Gmail)" >> .env
    echo "SMTP_HOST=smtp.gmail.com" >> .env
    echo "SMTP_PORT=587" >> .env
    echo "SMTP_USER=$USER_EMAIL" >> .env
    echo "SMTP_PASS=" >> .env

    echo -e "${GREEN}  ✅ Email configurado no .env${NC}"
    echo -e "${YELLOW}  ⚠️  IMPORTANTE: Configure SMTP_PASS manualmente${NC}"
    echo -e "${YELLOW}  Para Gmail, crie App Password: https://myaccount.google.com/apppasswords${NC}"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CRIAR TABELA JOBS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🗄️  [3/5] Criando tabela jobs...${NC}"

if psql -U sofia -d sofia_db -c "SELECT 1 FROM sofia.jobs LIMIT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Tabela sofia.jobs já existe${NC}"
else
    echo -e "${YELLOW}  ⏳ Criando tabela sofia.jobs...${NC}"

    if psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Tabela sofia.jobs criada com sucesso${NC}"
    else
        echo -e "${RED}  ❌ Erro ao criar tabela sofia.jobs${NC}"
        echo -e "${YELLOW}  Execute manualmente: psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql${NC}"
    fi
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. ADICIONAR SCRIPTS AO PACKAGE.JSON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📦 [4/5] Atualizando package.json...${NC}"

if grep -q "collect:jobs" package.json; then
    echo -e "${GREEN}  ✅ Scripts de jobs já existem no package.json${NC}"
else
    echo -e "${YELLOW}  ⏳ Adicionando scripts ao package.json...${NC}"

    # Backup
    cp package.json package.json.backup

    # Adicionar scripts (Python porque é mais fácil de manipular JSON)
    python3 - <<PYTHON_SCRIPT
import json

with open('package.json', 'r') as f:
    pkg = json.load(f)

if 'scripts' not in pkg:
    pkg['scripts'] = {}

pkg['scripts']['collect:jobs'] = 'tsx collectors/jobs-collector.ts'
pkg['scripts']['collect:jobs:brazil'] = 'tsx collectors/jobs-collector.ts --country=Brasil'
pkg['scripts']['collect:jobs:usa'] = 'tsx collectors/jobs-collector.ts --country=USA'

with open('package.json', 'w') as f:
    json.dump(pkg, f, indent=2)

print('  ✅ Scripts adicionados ao package.json')
PYTHON_SCRIPT

fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. TORNAR SCRIPTS EXECUTÁVEIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🔧 [5/5] Tornando scripts executáveis...${NC}"

chmod +x send-insights-email.sh
chmod +x generate-premium-insights-v2.sh

echo -e "${GREEN}  ✅ Scripts executáveis${NC}"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESUMO FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Setup Completo!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}📋 Próximos Passos:${NC}"
echo ""

echo -e "${BLUE}1. Configure SMTP_PASS no .env:${NC}"
echo -e "   Edite: ${CYAN}nano .env${NC}"
echo -e "   Para Gmail, crie App Password: ${CYAN}https://myaccount.google.com/apppasswords${NC}"
echo ""

echo -e "${BLUE}2. Teste collector de jobs:${NC}"
echo -e "   ${CYAN}npm run collect:jobs${NC}"
echo ""

echo -e "${BLUE}3. Teste envio de email:${NC}"
echo -e "   ${CYAN}bash send-insights-email.sh${NC}"
echo ""

echo -e "${BLUE}4. Adicione ao crontab (opcional):${NC}"
echo -e "   ${CYAN}crontab -e${NC}"
echo ""
echo -e "   Adicione as linhas:"
echo -e "   ${GREEN}# Jobs Collector - 20:00 UTC${NC}"
echo -e "   ${GREEN}0 20 * * * cd $SCRIPT_DIR && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1${NC}"
echo ""
echo -e "   ${GREEN}# Email Insights - 23:00 UTC (Seg-Sex)${NC}"
echo -e "   ${GREEN}0 23 * * 1-5 cd $SCRIPT_DIR && bash send-insights-email.sh >> /var/log/sofia-email.log 2>&1${NC}"
echo ""

echo -e "${BLUE}5. Leia a documentação completa:${NC}"
echo -e "   ${CYAN}cat SETUP-EMAIL-E-JOBS.md${NC}"
echo ""

echo -e "${GREEN}🎉 Tudo pronto para uso!${NC}"
echo ""
