#!/bin/bash
#
# Sofia Pulse - Script All-in-One
# Executa TUDO automaticamente e envia email
#

set -e  # Parar em caso de erro

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 SOFIA PULSE - EXECUÇÃO AUTOMÁTICA COMPLETA"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$BASE_DIR"

echo -e "${BLUE}📂 Diretório: $BASE_DIR${NC}"
echo ""

# 1. Carregar .env
echo -e "${BLUE}📋 [1/7] Carregando variáveis de ambiente...${NC}"
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo -e "${GREEN}  ✅ .env carregado${NC}"
else
    echo -e "${RED}  ❌ .env não encontrado!${NC}"
    exit 1
fi
echo ""

# 2. Ativar virtual environment
echo -e "${BLUE}🐍 [2/7] Ativando virtual environment...${NC}"
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
    echo -e "${GREEN}  ✅ Virtual environment ativo${NC}"
else
    echo -e "${YELLOW}  ⚠️  Criando virtual environment...${NC}"
    python3 -m venv venv-analytics
    source venv-analytics/bin/activate
    pip install -q psycopg2-binary python-dotenv google-generativeai
    echo -e "${GREEN}  ✅ Virtual environment criado e ativado${NC}"
fi
echo ""

# 3. Coletar TODOS os dados
echo -e "${BLUE}📊 [3/7] Coletando TODOS os dados (mercado, papers, patents, jobs, IPOs)...${NC}"
bash collect-all-data.sh 2>&1 | tail -20
echo -e "${GREEN}  ✅ Todos os dados coletados${NC}"
echo ""

# 4. Gerar insights v3.0 (Geo-localizado + Gemini + Macro + Anomalias)
echo -e "${BLUE}💎 [4/7] Gerando Premium Insights v3.0 (GEO + AI)...${NC}"
python3 generate-premium-insights-v3-REAL.py 2>&1 | tail -40
echo -e "${GREEN}  ✅ Insights v3.0 gerados (geo-localizados + AI)${NC}"
echo ""

# 5. Ver preview dos insights
echo -e "${BLUE}📊 [5/7] Preview dos Insights v3.0...${NC}"
echo -e "${YELLOW}──────────────────────────────────────────────────────────────${NC}"
head -80 analytics/premium-insights/latest-v3.txt 2>/dev/null || head -80 analytics/premium-insights/latest-geo.txt
echo -e "${YELLOW}──────────────────────────────────────────────────────────────${NC}"
echo ""

# 6. Enviar email
echo -e "${BLUE}📧 [6/7] Enviando email para $EMAIL_TO...${NC}"
export $(grep -v '^#' .env | xargs)
python3 send-email.py 2>&1
echo ""

# 7. Resumo final
echo -e "${BLUE}📈 [7/7] Resumo Final${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ TUDO CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}📊 Arquivos gerados:${NC}"
ls -lh analytics/premium-insights/*.{txt,csv} 2>/dev/null | awk '{print "   "$9" ("$5")"}'
echo ""

echo -e "${YELLOW}📧 Email enviado para: ${GREEN}$EMAIL_TO${NC}"
echo -e "${YELLOW}📂 Insights em: ${GREEN}analytics/premium-insights/${NC}"
echo ""

echo -e "${YELLOW}🎯 Próximos passos:${NC}"
echo -e "   1. Checar seu email: ${GREEN}$EMAIL_TO${NC}"
echo -e "   2. Baixar os CSVs anexos se quiser análise customizada"
echo -e "   3. Automatizar com crontab (ver CLAUDE.md)"
echo ""

echo -e "${GREEN}🎉 Pronto!${NC}"
