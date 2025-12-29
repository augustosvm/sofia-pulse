#!/bin/bash

###############################################################################
# Sofia Pulse - Gerador de Insights PREMIUM
# Cruza TODOS os dados para gerar insights vendáveis para colunistas
# E alimenta a base de conhecimento da Sofia IA (RAG)
###############################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}🚀 Sofia Pulse - Premium Insights Generator${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Verificar se venv existe
if [ ! -d "venv-analytics" ]; then
    echo -e "${RED}❌ Erro: venv-analytics não encontrado${NC}"
    echo -e "${YELLOW}Execute: bash setup-data-mining.sh${NC}"
    exit 1
fi

# Ativar virtual environment
echo -e "${BLUE}📦 Ativando virtual environment...${NC}"
source venv-analytics/bin/activate

# Executar gerador de insights
echo -e "${BLUE}🔍 Gerando insights premium...${NC}"
python3 generate-premium-insights.py

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Insights gerados com sucesso!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📁 Arquivos gerados em: analytics/premium-insights/${NC}"
echo -e "${YELLOW}📄 Visualizar: cat analytics/premium-insights/latest.txt${NC}"
echo -e "${YELLOW}🤖 RAG Sofia: Insights prontos para indexação${NC}"
echo ""
