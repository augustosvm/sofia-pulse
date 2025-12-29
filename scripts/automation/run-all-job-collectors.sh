#!/bin/bash
# Script para executar todos os coletores de vagas

echo "=========================================="
echo "🚀 Executando Todos os Coletores de Vagas"
echo "=========================================="

cd /home/ubuntu/sofia-pulse

# Array de coletores
collectors=(
  "collect-jobs-adzuna.ts"
  "collect-jobs-arbeitnow.ts"
  "collect-jobs-github.ts"
  "collect-jobs-himalayas.ts"
  "collect-jobs-themuse.ts"
  "collect-jobs-usajobs.ts"
  "collect-jobs-weworkremotely.ts"
)

total=${#collectors[@]}
success=0
failed=0

for collector in "${collectors[@]}"; do
  echo ""
  echo "=========================================="
  echo "📋 Executando: $collector"
  echo "=========================================="
  
  if npx tsx "scripts/$collector"; then
    echo "✅ $collector concluído"
    ((success++))
  else
    echo "❌ $collector falhou"
    ((failed++))
  fi
  
  # Delay entre coletores
  sleep 5
done

echo ""
echo "=========================================="
echo "📊 RESUMO FINAL"
echo "=========================================="
echo "Total: $total coletores"
echo "✅ Sucesso: $success"
echo "❌ Falhas: $failed"
echo "=========================================="
