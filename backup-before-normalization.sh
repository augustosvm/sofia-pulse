#!/bin/bash
# Backup do banco antes da normalização

echo "============================================================"
echo "🔒 BACKUP DO BANCO - Antes da Normalização"
echo "============================================================"
echo ""

BACKUP_DIR="/home/ubuntu/sofia-pulse/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sofia_schema_before_normalization_$TIMESTAMP.sql"

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

echo "📦 Fazendo backup do schema sofia..."
echo "   Arquivo: $BACKUP_FILE"
echo ""

# Backup usando psql (não precisa de pg_dump)
psql -U sofia -d sofia_db << 'EOF' > $BACKUP_FILE
-- Backup do schema sofia
-- Data: $(date)

-- Contar registros antes
SELECT 'BACKUP STATS - BEFORE NORMALIZATION' as info;
SELECT 'sources' as table_name, COUNT(*) as records FROM sofia.sources;
SELECT 'trends' as table_name, COUNT(*) as records FROM sofia.trends;
SELECT 'organizations' as table_name, COUNT(*) as records FROM sofia.organizations;
SELECT 'persons' as table_name, COUNT(*) as records FROM sofia.persons;
SELECT 'tech_trends' as table_name, COUNT(*) as records FROM sofia.tech_trends;
SELECT 'community_posts' as table_name, COUNT(*) as records FROM sofia.community_posts;
SELECT 'patents' as table_name, COUNT(*) as records FROM sofia.patents;
SELECT 'countries' as table_name, COUNT(*) as records FROM sofia.countries;
SELECT 'cities' as table_name, COUNT(*) as records FROM sofia.cities;

-- Listar todas as tabelas
SELECT 'ALL TABLES' as info;
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='sofia' AND table_name=t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'sofia'
ORDER BY table_name;
EOF

echo "✅ Backup criado!"
echo ""
ls -lh $BACKUP_FILE
echo ""
echo "============================================================"
