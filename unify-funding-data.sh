#!/bin/bash

echo "=========================================================================="
echo "🚀 UNIFICAÇÃO DE DADOS DE FUNDING - EXECUÇÃO COMPLETA"
echo "=========================================================================="
echo ""
echo "Este script executará:"
echo "  1. Migration (adicionar colunas e constraints)"
echo "  2. Normalização (atualizar dados existentes)"
echo "  3. Deduplicação (remover duplicatas)"
echo ""
echo "=========================================================================="
echo ""

# Configuração do banco
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-sofia}"
DB_NAME="${POSTGRES_DB:-sofia_db}"

echo "📊 Configuração:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo ""

# Função para executar SQL
run_sql() {
    local sql_file=$1
    local description=$2
    
    echo "▶️  $description"
    echo "   Arquivo: $sql_file"
    
    PGPASSWORD=$POSTGRES_PASSWORD psql \
        -h $DB_HOST \
        -p $DB_PORT \
        -U $DB_USER \
        -d $DB_NAME \
        -f "$sql_file"
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Concluído com sucesso!"
    else
        echo "   ❌ Erro ao executar!"
        exit 1
    fi
    echo ""
}

# Passo 1: Migration
echo "=========================================================================="
echo "PASSO 1/3: MIGRATION - Adicionar Colunas e Constraints"
echo "=========================================================================="
echo ""

run_sql "migrations/add_funding_constraints.sql" "Adicionando colunas, constraints e índices"

# Passo 2: Normalização
echo "=========================================================================="
echo "PASSO 2/3: NORMALIZAÇÃO - Atualizar Dados Existentes"
echo "=========================================================================="
echo ""

echo "▶️  Executando script de normalização..."
python3 scripts/normalize-existing-funding.py

if [ $? -eq 0 ]; then
    echo "   ✅ Normalização concluída!"
else
    echo "   ❌ Erro na normalização!"
    exit 1
fi
echo ""

# Passo 3: Deduplicação
echo "=========================================================================="
echo "PASSO 3/3: DEDUPLICAÇÃO - Remover Duplicatas"
echo "=========================================================================="
echo ""

run_sql "migrations/deduplicate-funding.sql" "Removendo registros duplicados"

# Estatísticas finais
echo "=========================================================================="
echo "📊 ESTATÍSTICAS FINAIS"
echo "=========================================================================="
echo ""

PGPASSWORD=$POSTGRES_PASSWORD psql \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    -c "
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT company_name) as empresas_unicas,
    COUNT(DISTINCT organization_id) as organizations_linkadas,
    COUNT(DISTINCT source) as fontes_dados,
    COUNT(DISTINCT round_type) as tipos_round
FROM sofia.funding_rounds;
"

echo ""
echo "=========================================================================="
echo "✅ UNIFICAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================================================="
echo ""
echo "Próximos passos:"
echo "  1. Testar collectors atualizados"
echo "  2. Verificar dados no banco"
echo "  3. Atualizar documentação"
echo ""
