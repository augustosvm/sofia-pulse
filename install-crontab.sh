#!/bin/bash

###############################################################################
# Sofia Pulse - Instalador de Crontab
# Instala todas as automações: Finance, Insights, Backup
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}📅 Sofia Pulse - Instalador de Crontab${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo -e "${BLUE}📁 Diretório detectado: ${SCRIPT_DIR}${NC}"
echo ""

# Verificar se scripts existem
echo -e "${BLUE}🔍 Verificando scripts necessários...${NC}"

MISSING=0

if [ ! -f "${SCRIPT_DIR}/generate-premium-insights.sh" ]; then
    echo -e "${RED}❌ generate-premium-insights.sh não encontrado${NC}"
    MISSING=1
else
    echo -e "${GREEN}✅ generate-premium-insights.sh${NC}"
fi

if [ ! -f "${SCRIPT_DIR}/scripts/backup-complete.sh" ]; then
    echo -e "${YELLOW}⚠️  scripts/backup-complete.sh não encontrado (opcional)${NC}"
else
    echo -e "${GREEN}✅ scripts/backup-complete.sh${NC}"
fi

echo ""

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}❌ Faltam scripts necessários. Abortando.${NC}"
    exit 1
fi

# Criar crontab
echo -e "${BLUE}📋 Gerando crontab...${NC}"

CRON_FILE="/tmp/sofia-crontab-$$.tmp"

cat > "$CRON_FILE" << EOF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sofia Pulse - Automações Completas
# Instalado em: $(date)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. FINANCE COLLECTORS (Segunda a Sexta)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# B3 (Brasil) - 21:00 UTC (18:00 BRT)
0 21 * * 1-5 cd ${SCRIPT_DIR} && npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1

# NASDAQ (USA) - 21:05 UTC
5 21 * * 1-5 cd ${SCRIPT_DIR} && npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1

# Funding Rounds - 21:10 UTC
10 21 * * * cd ${SCRIPT_DIR} && npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. PREMIUM INSIGHTS (Segunda a Sexta)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Gerar insights - 22:00 UTC
0 22 * * 1-5 cd ${SCRIPT_DIR} && ./generate-premium-insights.sh >> /var/log/sofia-insights.log 2>&1

EOF

# Adicionar backup se existir
if [ -f "${SCRIPT_DIR}/scripts/backup-complete.sh" ]; then
cat >> "$CRON_FILE" << EOF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. BACKUP COMPLETO (Diário)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Backup - 04:00 UTC
0 4 * * * ${SCRIPT_DIR}/scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1

EOF
fi

cat >> "$CRON_FILE" << EOF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. LIMPEZA DE LOGS (Semanal)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Limpar logs antigos - Domingo 05:00 UTC
0 5 * * 0 find /var/log/sofia-*.log -mtime +30 -delete

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo -e "${GREEN}✅ Crontab gerado em: ${CRON_FILE}${NC}"
echo ""

# Mostrar preview
echo -e "${BLUE}📄 Preview do crontab:${NC}"
echo -e "${YELLOW}────────────────────────────────────────────────────────────────${NC}"
cat "$CRON_FILE" | grep -v "^#" | grep -v "^$"
echo -e "${YELLOW}────────────────────────────────────────────────────────────────${NC}"
echo ""

# Perguntar confirmação
echo -e "${YELLOW}⚠️  Isso vai SUBSTITUIR seu crontab atual!${NC}"
echo -e "${BLUE}Deseja instalar? (y/n)${NC}"
read -r -p "> " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Instalação cancelada${NC}"
    rm "$CRON_FILE"
    exit 0
fi

# Fazer backup do crontab atual
echo ""
echo -e "${BLUE}📦 Fazendo backup do crontab atual...${NC}"
BACKUP_FILE="${SCRIPT_DIR}/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "(crontab estava vazio)" > "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup salvo em: ${BACKUP_FILE}${NC}"
echo ""

# Instalar novo crontab
echo -e "${BLUE}🚀 Instalando novo crontab...${NC}"
crontab "$CRON_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Crontab instalado com sucesso!${NC}"
else
    echo -e "${RED}❌ Erro ao instalar crontab${NC}"
    rm "$CRON_FILE"
    exit 1
fi

# Limpar arquivo temporário
rm "$CRON_FILE"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Instalação Completa!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Mostrar crontab instalado
echo -e "${BLUE}📋 Crontab instalado:${NC}"
crontab -l

echo ""
echo -e "${YELLOW}📊 Próximas Execuções (UTC):${NC}"
echo -e "   21:00 (Seg-Sex): Finance B3"
echo -e "   21:05 (Seg-Sex): Finance NASDAQ"
echo -e "   21:10 (Diário):  Finance Funding"
echo -e "   22:00 (Seg-Sex): Premium Insights"
if [ -f "${SCRIPT_DIR}/scripts/backup-complete.sh" ]; then
    echo -e "   04:00 (Diário):  Backup Completo"
fi
echo -e "   05:00 (Domingo): Limpeza Logs"
echo ""

echo -e "${YELLOW}📝 Monitorar logs:${NC}"
echo -e "   tail -f /var/log/sofia-finance-b3.log"
echo -e "   tail -f /var/log/sofia-insights.log"
echo ""

echo -e "${GREEN}🎉 Automação configurada com sucesso!${NC}"
