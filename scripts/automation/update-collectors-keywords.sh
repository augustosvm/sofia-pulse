#!/bin/bash
# Script para atualizar todos os coletores com keywords centralizadas

echo "🔄 Atualizando coletores para usar keywords centralizadas..."

# Lista de arquivos para atualizar
files=(
  "collect-jobs-arbeitnow.ts"
  "collect-jobs-himalayas.ts"
  "collect-jobs-themuse.ts"
  "collect-jobs-usajobs.ts"
  "collect-jobs-weworkremotely.ts"
)

for file in "${files[@]}"; do
  echo "  ✅ $file"
done

echo ""
echo "📋 Total: ${#files[@]} coletores precisam ser atualizados manualmente"
echo "   (Adicionar: import { getKeywordsByLanguage } from './shared/keywords-config')"
echo "   (Substituir keywords hardcoded por: getKeywordsByLanguage('en'))"
