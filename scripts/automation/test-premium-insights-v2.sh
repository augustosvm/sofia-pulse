#!/bin/bash

###############################################################################
# Sofia Pulse - Validador Premium Insights v2.0
# Testa se a instalação v2.0 está correta e funcionando
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
echo -e "  ${GREEN}🧪 Sofia Pulse - Teste Premium Insights v2.0${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

ERRORS=0
WARNINGS=0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. VERIFICAR ARQUIVOS NECESSÁRIOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📁 [1/6] Verificando arquivos...${NC}"

FILES=(
    "generate-premium-insights-v2.py"
    "generate-premium-insights-v2.sh"
    "collectors/ipo-calendar.ts"
    "db/migrations/007_create_ipo_calendar.sql"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ $file NÃO ENCONTRADO${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. VERIFICAR VIRTUAL ENVIRONMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🐍 [2/6] Verificando virtual environment...${NC}"

if [ -d "venv-analytics" ]; then
    echo -e "${GREEN}  ✅ venv-analytics encontrado${NC}"

    # Ativar venv e verificar pacotes
    source venv-analytics/bin/activate

    PACKAGES=("pandas" "psycopg2" "google-generativeai")

    for pkg in "${PACKAGES[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            echo -e "${GREEN}  ✅ Python package: $pkg${NC}"
        else
            echo -e "${RED}  ❌ Python package FALTANDO: $pkg${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done
else
    echo -e "${RED}  ❌ venv-analytics NÃO ENCONTRADO${NC}"
    echo -e "${YELLOW}  ⚠️  Execute: bash setup-data-mining.sh${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. VERIFICAR BANCO DE DADOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🗄️  [3/6] Verificando banco de dados...${NC}"

# Verificar conexão PostgreSQL
if psql -U sofia -d sofia_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Conexão PostgreSQL OK${NC}"

    # Verificar tabelas necessárias
    TABLES=(
        "sofia.stackoverflow_trends"
        "sofia.github_metrics"
        "sofia.publications"
        "sofia.startups"
        "sofia.funding_rounds"
        "sofia.market_data_brazil"
        "sofia.market_data_nasdaq"
        "sofia.ipo_calendar"
    )

    for table in "${TABLES[@]}"; do
        COUNT=$(psql -U sofia -d sofia_db -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
        COUNT=$(echo $COUNT | xargs) # trim whitespace

        if [ "$COUNT" = "0" ] 2>/dev/null; then
            echo -e "${YELLOW}  ⚠️  $table: 0 registros (vazio)${NC}"
            WARNINGS=$((WARNINGS + 1))
        elif [ -z "$COUNT" ]; then
            echo -e "${RED}  ❌ $table: TABELA NÃO EXISTE${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${GREEN}  ✅ $table: $COUNT registros${NC}"
        fi
    done
else
    echo -e "${RED}  ❌ Falha ao conectar no PostgreSQL${NC}"
    echo -e "${YELLOW}  ⚠️  Verifique se PostgreSQL está rodando${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. VERIFICAR GEMINI API KEY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🤖 [4/6] Verificando Gemini API...${NC}"

if [ -f ".env" ]; then
    if grep -q "GEMINI_API_KEY" .env; then
        GEMINI_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")

        if [ -z "$GEMINI_KEY" ] || [ "$GEMINI_KEY" = "your-key" ]; then
            echo -e "${RED}  ❌ GEMINI_API_KEY não configurada${NC}"
            echo -e "${YELLOW}  ⚠️  Narrativas AI não serão geradas${NC}"
            echo -e "${YELLOW}  ⚠️  Configure: echo 'GEMINI_API_KEY=sua-chave' >> .env${NC}"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${GREEN}  ✅ GEMINI_API_KEY configurada${NC}"
        fi
    else
        echo -e "${RED}  ❌ GEMINI_API_KEY não encontrada no .env${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}  ⚠️  Arquivo .env não encontrado${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. TESTAR EXECUÇÃO DO SCRIPT V2
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}🚀 [5/6] Testando geração de insights v2...${NC}"

if [ -f "generate-premium-insights-v2.sh" ]; then
    chmod +x generate-premium-insights-v2.sh

    echo -e "${YELLOW}  ⏳ Executando generate-premium-insights-v2.sh...${NC}"

    if ./generate-premium-insights-v2.sh > /tmp/test-v2-output.log 2>&1; then
        echo -e "${GREEN}  ✅ Script executado com sucesso${NC}"

        # Verificar arquivos de output gerados
        if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
            echo -e "${GREEN}  ✅ Arquivo latest-geo.txt gerado${NC}"
        else
            echo -e "${RED}  ❌ Arquivo latest-geo.txt NÃO gerado${NC}"
            ERRORS=$((ERRORS + 1))
        fi

        if [ -f "analytics/premium-insights/latest-geo.md" ]; then
            echo -e "${GREEN}  ✅ Arquivo latest-geo.md gerado${NC}"
        else
            echo -e "${YELLOW}  ⚠️  Arquivo latest-geo.md NÃO gerado${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi

        if [ -f "analytics/premium-insights/geo-summary.csv" ]; then
            echo -e "${GREEN}  ✅ Arquivo geo-summary.csv gerado${NC}"
        else
            echo -e "${YELLOW}  ⚠️  Arquivo geo-summary.csv NÃO gerado${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "${RED}  ❌ Erro ao executar script${NC}"
        echo -e "${YELLOW}  📄 Ver log: cat /tmp/test-v2-output.log${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}  ❌ generate-premium-insights-v2.sh não encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. PREVIEW DOS INSIGHTS GERADOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}📊 [6/6] Preview dos insights gerados...${NC}"

if [ -f "analytics/premium-insights/latest-geo.txt" ]; then
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    head -30 analytics/premium-insights/latest-geo.txt
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"

    LINES=$(wc -l < analytics/premium-insights/latest-geo.txt)
    echo -e "${GREEN}  ✅ Total de linhas: $LINES${NC}"
    echo -e "${YELLOW}  📄 Ver completo: cat analytics/premium-insights/latest-geo.txt${NC}"
else
    echo -e "${RED}  ❌ Nenhum insight gerado ainda${NC}"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESUMO FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${BLUE}📊 RESUMO DO TESTE${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ TUDO OK! Premium Insights v2.0 está funcionando perfeitamente!${NC}"
    echo ""
    echo -e "${YELLOW}📁 Próximos passos:${NC}"
    echo -e "   1. Ver insights: ${CYAN}cat analytics/premium-insights/latest-geo.txt${NC}"
    echo -e "   2. Instalar crontab: ${CYAN}bash install-crontab.sh${NC}"
    echo -e "   3. Monitorar logs: ${CYAN}tail -f /var/log/sofia-insights.log${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  AVISOS: $WARNINGS${NC}"
    echo -e "${GREEN}✅ Sem erros críticos${NC}"
    echo ""
    echo -e "${YELLOW}Recomendações:${NC}"
    echo -e "   - Configure GEMINI_API_KEY para narrativas AI"
    echo -e "   - Execute collectors para popular o banco"
    exit 0
else
    echo -e "${RED}❌ ERROS ENCONTRADOS: $ERRORS${NC}"
    echo -e "${YELLOW}⚠️  AVISOS: $WARNINGS${NC}"
    echo ""
    echo -e "${YELLOW}Ações necessárias:${NC}"

    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}   - Corrija os erros listados acima${NC}"
        echo -e "${RED}   - Verifique se todos os arquivos foram commitados${NC}"
        echo -e "${RED}   - Execute: git pull${NC}"
    fi

    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}   - Configure GEMINI_API_KEY (opcional mas recomendado)${NC}"
        echo -e "${YELLOW}   - Execute collectors para popular dados${NC}"
    fi

    exit 1
fi

echo ""
