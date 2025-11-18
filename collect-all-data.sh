#!/bin/bash
#
# Sofia Pulse - Collector Completo
# Executa TODOS os collectors para popular o banco
#

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 SOFIA PULSE - COLETA COMPLETA DE DADOS"
echo "════════════════════════════════════════════════════════════════"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$BASE_DIR"

# ============================================================================
# 1. MERCADO FINANCEIRO
# ============================================================================

echo -e "${BLUE}📊 [1/6] Coletando dados de mercado financeiro...${NC}"

cd finance

echo -e "  → B3 (Brasil)..."
npm run collect:brazil 2>&1 | grep -E "(Coletando|ações|salvas|Concluída)" || true

echo -e "  → NASDAQ (USA)..."
npm run collect:nasdaq 2>&1 | grep -E "(Coletando|ações|salvas|Concluída)" || true

echo -e "  → Funding Rounds..."
npm run collect:funding 2>&1 | grep -E "(Coletando|rodadas|salvas|Concluída)" || true

cd "$BASE_DIR"
echo -e "${GREEN}  ✅ Mercado financeiro coletado${NC}\n"

# ============================================================================
# 2. PESQUISA ACADÊMICA
# ============================================================================

echo -e "${BLUE}📚 [2/6] Coletando papers acadêmicos...${NC}"

echo -e "  → ArXiv (AI/ML papers)..."
npx tsx scripts/collect-arxiv-ai.ts 2>&1 | grep -E "(Coletando|papers|salvo|Found)" || true

echo -e "  → OpenAlex (papers globais)..."
npx tsx scripts/collect-openalex.ts 2>&1 | grep -E "(Coletando|papers|salvo|Found)" || true

echo -e "${GREEN}  ✅ Papers acadêmicos coletados${NC}\n"

# ============================================================================
# 3. PROPRIEDADE INTELECTUAL
# ============================================================================

echo -e "${BLUE}📜 [3/6] Coletando patents...${NC}"

echo -e "  → EPO (European Patent Office)..."
npx tsx scripts/collect-epo-patents.ts 2>&1 | grep -E "(Coletando|patents|salvo|Found)" || true

echo -e "  → WIPO China..."
npx tsx scripts/collect-wipo-china-patents.ts 2>&1 | grep -E "(Coletando|patents|salvo|Found)" || true

echo -e "${GREEN}  ✅ Patents coletados${NC}\n"

# ============================================================================
# 4. STARTUPS E EMPRESAS
# ============================================================================

echo -e "${BLUE}🚀 [4/6] Coletando dados de startups...${NC}"

echo -e "  → AI Companies..."
npx tsx scripts/collect-ai-companies.ts 2>&1 | grep -E "(Coletando|companies|salvo|Found)" || true

echo -e "${GREEN}  ✅ Startups coletadas${NC}\n"

# ============================================================================
# 5. MERCADO DE TRABALHO
# ============================================================================

echo -e "${BLUE}💼 [5/6] Coletando vagas de emprego...${NC}"

echo -e "  → Jobs (Indeed, LinkedIn, AngelList)..."
npx tsx collectors/jobs-collector.ts 2>&1 | grep -E "(Coletando|vagas|salvo|Found)" || true

echo -e "${GREEN}  ✅ Vagas coletadas${NC}\n"

# ============================================================================
# 6. IPOS
# ============================================================================

echo -e "${BLUE}💰 [6/6] Coletando IPOs futuros...${NC}"

echo -e "  → IPO Calendar (NASDAQ, B3, HKEX)..."
npx tsx collectors/ipo-calendar.ts 2>&1 | grep -E "(Coletando|IPOs|salvo|Found)" || true

echo -e "  → HKEX IPOs..."
npx tsx scripts/collect-hkex-ipos.ts 2>&1 | grep -E "(Coletando|IPOs|salvo|Found)" || true

echo -e "${GREEN}  ✅ IPOs coletados${NC}\n"

# ============================================================================
# RESUMO
# ============================================================================

echo -e "${BLUE}📊 RESUMO DA COLETA${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"

# Contar registros no banco (se psql disponível)
if command -v psql &> /dev/null; then
    export PGPASSWORD=$DB_PASSWORD
    echo ""
    psql -h localhost -U $DB_USER -d $DB_NAME -c "
        SELECT
            'Funding Rounds' as dataset,
            COUNT(*) as records
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days'
        UNION ALL
        SELECT
            'B3 Stocks',
            COUNT(DISTINCT ticker)
        FROM market_data_brazil
        WHERE collected_at >= CURRENT_DATE - INTERVAL '7 days'
        UNION ALL
        SELECT
            'NASDAQ Stocks',
            COUNT(DISTINCT ticker)
        FROM market_data_nasdaq
        WHERE collected_at >= CURRENT_DATE - INTERVAL '7 days'
        UNION ALL
        SELECT
            'Jobs',
            COUNT(*)
        FROM sofia.jobs
        WHERE posted_date >= CURRENT_DATE - INTERVAL '30 days'
        UNION ALL
        SELECT
            'IPO Calendar',
            COUNT(*)
        FROM sofia.ipo_calendar
        WHERE expected_date >= CURRENT_DATE
    " 2>/dev/null || echo "  (não foi possível conectar ao banco para contagem)"
fi

echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ COLETA COMPLETA CONCLUÍDA!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Próximo passo:${NC}"
echo -e "  bash run-all.sh  ${BLUE}# Gerar insights + enviar email${NC}"
echo ""
