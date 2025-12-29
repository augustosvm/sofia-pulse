#!/bin/bash

################################################################################
# Fix: Git Pull + Setup Completo
################################################################################

set -e

cd ~/sofia-pulse

echo "════════════════════════════════════════════════════════════════"
echo "🔧 FIX: Git Pull + Setup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Remove arquivos não rastreados
echo "1️⃣  Removendo arquivos não rastreados..."
rm -f analytics/causal-insights-latest.txt
rm -f analytics/dark-horses-latest.txt
rm -f analytics/early-stage-latest.txt
rm -f analytics/mega-analysis-latest.txt
rm -f analytics/special-sectors-latest.txt
echo "   ✅ Arquivos removidos"
echo ""

# 2. Git pull
echo "2️⃣  Git pull..."
git pull origin claude/fix-github-rate-limits-012Xm4nfg6i34xKQHSDbWfq3
echo "   ✅ Pull complete"
echo ""

# 3. Verificar se update-crontab-distributed.sh existe
echo "3️⃣  Verificando scripts..."
if [ -f "update-crontab-distributed.sh" ]; then
    echo "   ✅ update-crontab-distributed.sh encontrado"
else
    echo "   ⚠️  update-crontab-distributed.sh não encontrado"
    echo "   Script está no branch, executando git pull novamente..."
    git fetch origin
    git checkout claude/fix-github-rate-limits-012Xm4nfg6i34xKQHSDbWfq3
    git pull
fi
echo ""

# 4. Verificar GITHUB_TOKEN
echo "4️⃣  Verificando GITHUB_TOKEN..."
if grep -q "GITHUB_TOKEN" .env; then
    echo "   ✅ GITHUB_TOKEN configurado"
else
    echo "   ⚠️  GITHUB_TOKEN não encontrado em .env"
    echo "   Adicione com: echo 'GITHUB_TOKEN=seu_token' >> .env"
    echo "   Obter em: https://github.com/settings/tokens"
fi
echo ""

# 5. Listar scripts criados
echo "5️⃣  Scripts disponíveis:"
ls -lh collect-fast-apis.sh collect-limited-apis.sh update-crontab-distributed.sh 2>/dev/null || echo "   ⚠️  Alguns scripts não encontrados"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ FIX COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Próximos Passos:"
echo ""
echo "1. Configurar GITHUB_TOKEN (se não configurado):"
echo "   echo 'GITHUB_TOKEN=ghp_seu_token_aqui' >> .env"
echo ""
echo "2. Aplicar crontab distribuído:"
echo "   bash update-crontab-distributed.sh"
echo ""
echo "3. OU executar manualmente:"
echo "   bash collect-fast-apis.sh"
echo "   bash collect-limited-apis.sh"
echo "   bash run-mega-analytics.sh && bash send-email-mega.sh"
echo ""
