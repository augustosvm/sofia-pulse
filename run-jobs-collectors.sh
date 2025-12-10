#!/bin/bash
# Script para executar todos os coletores de vagas
# Autor: Sofia Pulse
# Data: 2025-12-10

cd /home/ubuntu/sofia-pulse || exit 1

echo "======================================================================"
echo "SOFIA PULSE - Coleta de Vagas Tech"
echo "Iniciado em: $(date)"
echo "======================================================================"

# Ativar venv se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

TOTAL_COLLECTED=0

# Lista de coletores (APIs públicas, sem necessidade de chaves)
COLLECTORS=(
    "scripts/collect-jobs-arbeitnow.ts"
    "scripts/collect-jobs-themuse.ts"
    "scripts/collect-jobs-github.ts"
    "scripts/collect-jobs-himalayas.ts"
    "scripts/collect-jobs-weworkremotely.ts"
)

for collector in "${COLLECTORS[@]}"; do
    if [ -f "$collector" ]; then
        echo ""
        echo "----------------------------------------------------------------------"
        echo "Executando: $collector"
        echo "----------------------------------------------------------------------"
        
        # Executar com node --import tsx (Node 20+)
        if node --import tsx "$collector" 2>&1; then
            echo "✅ $collector concluído com sucesso"
        else
            echo "❌ $collector falhou"
        fi
    else
        echo "⚠️  Arquivo não encontrado: $collector"
    fi
done

echo ""
echo "======================================================================"
echo "Coleta finalizada em: $(date)"
echo "======================================================================"
