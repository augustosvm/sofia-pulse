#!/bin/bash
# Script para executar todos os coletores de vagas que requerem API key

echo "🚀 Executando coletores de vagas com API key..."
echo "============================================================"

# Himalayas (corrigido - não requer API key)
echo ""
echo "🏔️ Coletando Himalayas..."
npx tsx scripts/collect-jobs-himalayas.ts

# Adzuna (requer API key)
echo ""
echo "💼 Coletando Adzuna..."
npx tsx scripts/collect-jobs-adzuna.ts

# USAJOBS (requer API key)
echo ""
echo "🏛️ Coletando USAJOBS..."
npx tsx scripts/collect-jobs-usajobs.ts

echo ""
echo "============================================================"
echo "✅ Coleta concluída!"
echo ""
echo "📊 Verificar resultados:"
echo "psql -U sofia -d sofia_db -c \"SELECT platform, COUNT(*) FROM sofia.jobs WHERE platform IN ('himalayas', 'adzuna', 'usajobs') GROUP BY platform;\""
