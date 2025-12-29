#!/bin/bash

#============================================================================
# Sofia Pulse - Finance Collectors (Automated)
#============================================================================
# Coleta dados de mercado:
# - B3 (Brasil): Stocks brasileiras
# - NASDAQ: High-momentum tech stocks
# - Funding Rounds: VC/PE deals
#
# Uso:
#   ./collect-finance.sh
#
# Crontab recomendado:
#   0 21 * * 1-5 /home/ubuntu/sofia-pulse/collect-finance.sh >> /var/log/sofia-finance-complete.log 2>&1
#============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🔹 Sofia Pulse - Finance Collectors${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Started: $TIMESTAMP"
echo ""

# Change to sofia-pulse directory
cd /home/ubuntu/sofia-pulse || {
  echo -e "${RED}❌ Erro: Diretório /home/ubuntu/sofia-pulse não encontrado${NC}"
  exit 1
}

# Create logs directory if not exists
mkdir -p logs

# Counters
SUCCESS_COUNT=0
FAIL_COUNT=0

#============================================================================
# 1. B3 Stocks (Brasil)
#============================================================================
echo -e "${BLUE}📊 [1/3] Coletando B3 (Brasil)...${NC}"

npm run collect:brazil >> logs/finance-b3.log 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "   ${GREEN}✅ B3: Sucesso${NC}"
  ((SUCCESS_COUNT++))
else
  echo -e "   ${RED}❌ B3: Falhou (exit code: $EXIT_CODE)${NC}"
  echo -e "   ${YELLOW}Ver log: logs/finance-b3.log${NC}"
  ((FAIL_COUNT++))
fi

#============================================================================
# 2. NASDAQ (Rate Limit Protection)
#============================================================================
echo ""
echo -e "${BLUE}📊 [2/3] Coletando NASDAQ...${NC}"
echo -e "   ${YELLOW}⏱️  Aguardando 60s (Alpha Vantage rate limit)...${NC}"

sleep 60

npm run collect:nasdaq >> logs/finance-nasdaq.log 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "   ${GREEN}✅ NASDAQ: Sucesso${NC}"
  ((SUCCESS_COUNT++))
else
  echo -e "   ${RED}❌ NASDAQ: Falhou (exit code: $EXIT_CODE)${NC}"
  echo -e "   ${YELLOW}Ver log: logs/finance-nasdaq.log${NC}"
  ((FAIL_COUNT++))
fi

#============================================================================
# 3. Funding Rounds
#============================================================================
echo ""
echo -e "${BLUE}💰 [3/3] Coletando Funding Rounds...${NC}"

npm run collect:funding >> logs/finance-funding.log 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "   ${GREEN}✅ Funding: Sucesso${NC}"
  ((SUCCESS_COUNT++))
else
  echo -e "   ${RED}❌ Funding: Falhou (exit code: $EXIT_CODE)${NC}"
  echo -e "   ${YELLOW}Ver log: logs/finance-funding.log${NC}"
  ((FAIL_COUNT++))
fi

#============================================================================
# Summary
#============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 Resumo da Coleta${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Sucesso: $SUCCESS_COUNT/3${NC}"
echo -e "${RED}❌ Falhas:  $FAIL_COUNT/3${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
  echo -e "${GREEN}✅ Finance Collectors - Todos os dados coletados com sucesso!${NC}"
  EXIT_STATUS=0
else
  echo -e "${YELLOW}⚠️  Finance Collectors - Alguns collectors falharam${NC}"
  echo -e "${YELLOW}   Verificar logs em ~/sofia-pulse/logs/finance-*.log${NC}"
  EXIT_STATUS=1
fi

TIMESTAMP_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "Finished: $TIMESTAMP_END"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_STATUS
