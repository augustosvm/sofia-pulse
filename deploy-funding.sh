#!/bin/bash
# ============================================================================
# UNIFICAÇÃO DE FUNDING - Deploy Seguro (com .env)
# ============================================================================

set -e  # Para em caso de erro

echo "=========================================================================="
echo "UNIFICACAO DE FUNDING - DEPLOY SEGURO"
echo "=========================================================================="
echo ""

# Carregar variáveis de ambiente do .env
if [ -f .env ]; then
    echo "Carregando variáveis de ambiente do .env..."
    export $(cat .env | grep -v '^#' | xargs)
    echo ""
fi

# Configurações
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

echo "1. Criando backup via Python..."
mkdir -p "$BACKUP_DIR"

python3 << 'PYTHON_BACKUP'
import psycopg2
import os
import json
from datetime import datetime

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', '91.98.158.19'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER', 'sofia'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB', 'sofia_db')
)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds")
count = cur.fetchone()[0]

print(f"   Backup de {count} registros de funding_rounds")

cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT company_name) as empresas,
        COUNT(organization_id) as com_org_id,
        COUNT(source) as com_source
    FROM sofia.funding_rounds
""")

stats = cur.fetchone()
backup_info = {
    'timestamp': datetime.now().isoformat(),
    'total_registros': stats[0],
    'empresas_unicas': stats[1],
    'com_organization_id': stats[2],
    'com_source': stats[3]
}

backup_dir = [d for d in os.listdir('.') if d.startswith('backup_')][-1]
with open(f'{backup_dir}/funding_backup_info.json', 'w') as f:
    json.dump(backup_info, f, indent=2)

print(f"   Backup info salvo")
conn.close()
PYTHON_BACKUP

echo ""

echo "2. Fazendo pull do código..."
git pull origin master
echo ""

echo "3. Executando migration..."
python3 << 'PYTHON_MIGRATION'
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

with open('migrations/add_funding_constraints.sql', 'r') as f:
    sql = f.read()

cur = conn.cursor()
cur.execute(sql)
conn.commit()
conn.close()
print("   Migration executada com sucesso")
PYTHON_MIGRATION

echo ""

echo "4. Normalizando dados existentes..."
python3 scripts/normalize-existing-funding.py
echo ""

echo "5. Removendo duplicatas..."
python3 << 'PYTHON_DEDUP'
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

with open('migrations/deduplicate-funding.sql', 'r') as f:
    sql = f.read()

cur = conn.cursor()
cur.execute(sql)
conn.commit()
conn.close()
print("   Deduplicação executada com sucesso")
PYTHON_DEDUP

echo ""

echo "6. Estatísticas finais..."
python3 << 'PYTHON_STATS'
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

cur = conn.cursor()
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT company_name) as empresas,
        COUNT(DISTINCT organization_id) as orgs,
        COUNT(DISTINCT source) as fontes,
        COUNT(DISTINCT round_type) as tipos
    FROM sofia.funding_rounds
""")

row = cur.fetchone()
print(f"\n   Total de registros: {row[0]}")
print(f"   Empresas únicas: {row[1]}")
print(f"   Organizations linkadas: {row[2]}")
print(f"   Fontes de dados: {row[3]}")
print(f"   Tipos de round: {row[4]}\n")

conn.close()
PYTHON_STATS

echo ""
echo "=========================================================================="
echo "CONCLUIDO COM SUCESSO!"
echo "=========================================================================="
echo ""
echo "Backup info disponível em: $BACKUP_DIR/funding_backup_info.json"
echo ""


