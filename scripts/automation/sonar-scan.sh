#!/bin/bash
# ============================================================================
# SonarCloud Analysis - Active Code Only
# ============================================================================
# Analisa apenas os 16.5k linhas de código ativo
# Ignora 4.5k linhas de scripts legacy/one-time
# ============================================================================

echo "=========================================================================="
echo "SONARCLOUD ANALYSIS - ACTIVE CODE ONLY"
echo "=========================================================================="
echo ""

# Carregar .env se existir
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Verificar token
if [ -z "$SONAR_TOKEN" ]; then
    echo "❌ SONAR_TOKEN não configurado!"
    echo ""
    echo "Configure com:"
    echo "  export SONAR_TOKEN='seu_token_aqui'"
    echo "  ou adicione ao .env"
    exit 1
fi

# Contar linhas de código ativo
echo "📊 Contando linhas de código ativo..."
echo ""

COLLECTORS=$(find scripts -name "collect-*.py" -not -path "*/legacy/*" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
HELPERS=$(find scripts/shared -name "*.py" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
WHATSAPP=$(wc -l scripts/utils/sofia_whatsapp_integration.py 2>/dev/null | awk '{print $1}')
TS_CORE=$(wc -l scripts/collect.ts scripts/generate-crontab.ts 2>/dev/null | tail -1 | awk '{print $1}')

TOTAL_ACTIVE=$((COLLECTORS + HELPERS + WHATSAPP + TS_CORE))

echo "   Collectors Python: $COLLECTORS linhas (55 arquivos)"
echo "   Helpers: $HELPERS linhas (geo, org, funding)"
echo "   WhatsApp Integration: $WHATSAPP linhas"
echo "   TypeScript Core: $TS_CORE linhas"
echo "   ────────────────────────────────"
echo "   TOTAL ATIVO: $TOTAL_ACTIVE linhas"
echo ""

# Gerar relatório Pylint (apenas código ativo)
echo "📝 Gerando relatório Pylint..."

pylint \
  scripts/collect-*.py \
  scripts/shared/*.py \
  scripts/utils/sofia_whatsapp_integration.py \
  --output-format=json \
  --exit-zero \
  > pylint-report.json 2>/dev/null

PYLINT_ISSUES=$(cat pylint-report.json | grep -c "\"type\":" || echo "0")
echo "   Pylint: $PYLINT_ISSUES issues encontrados"
echo ""

# Executar SonarScanner
echo "🚀 Enviando para SonarCloud..."
echo ""

sonar-scanner \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.login=$SONAR_TOKEN

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================================================="
    echo "✅ ANÁLISE CONCLUÍDA COM SUCESSO!"
    echo "=========================================================================="
    echo ""
    echo "📊 Dashboard: https://sonarcloud.io/dashboard?id=augustosvm_sofia-pulse"
    echo ""
    echo "🎯 Código Analisado ($TOTAL_ACTIVE linhas):"
    echo "   ✅ 55 Collectors Python (~14,755 linhas)"
    echo "   ✅ 3 Helpers (geo, org, funding) (~900 linhas)"
    echo "   ✅ WhatsApp Integration (~423 linhas)"
    echo "   ✅ TypeScript Core (~548 linhas)"
    echo ""
    echo "🚫 Código Ignorado (~4,500 linhas):"
    echo "   ❌ Legacy/One-time scripts (115 arquivos)"
    echo "   ❌ SQL Migrations (101 arquivos)"
    echo "   ❌ Scripts de automação (140 arquivos)"
    echo "   ❌ Documentação (104 arquivos)"
    echo ""
else
    echo ""
    echo "❌ Erro na análise!"
    echo "Verifique:"
    echo "  1. SONAR_TOKEN está correto"
    echo "  2. sonar-scanner está instalado"
    echo "  3. Conexão com internet"
    exit 1
fi
