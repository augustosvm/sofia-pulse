#!/bin/bash

###############################################################################
# Sofia Pulse - Gerador de Insights PREMIUM v2.0
# ANÁLISE GEOGRÁFICA + NARRATIVAS RICAS
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}🌍 Sofia Pulse - Premium Insights v2.0 (GEO-LOCALIZADOS)${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
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

# Executar gerador de insights v2
echo -e "${CYAN}🌍 Gerando insights GEO-LOCALIZADOS...${NC}"
python3 generate-premium-insights-v2.py

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Insights GEO-LOCALIZADOS gerados com sucesso!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📁 Arquivos gerados em: analytics/premium-insights/${NC}"
echo -e "${YELLOW}📄 Visualizar: cat analytics/premium-insights/latest-geo.txt${NC}"
echo -e "${YELLOW}🗺️  Mapa Global: analytics/premium-insights/geo-summary.csv${NC}"
echo ""
echo -e "${GREEN}🎯 Novidades v2.0:${NC}"
echo -e "   ✅ Análise por continente/país"
echo -e "   ✅ Especialização regional"
echo -e "   ✅ Texto narrativo pronto para copiar"
echo -e "   ✅ Universidades e suas expertises"
echo ""
