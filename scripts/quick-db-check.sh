#!/bin/bash
# ============================================================================
# VERIFICAÇÃO RÁPIDA DO BANCO - Sofia Pulse
# ============================================================================
# Execute: bash scripts/quick-db-check.sh
# ============================================================================

echo "🔍 QUICK DATABASE CHECK"
echo "============================================================================"
echo ""

echo "1️⃣ Verificando conexão PostgreSQL..."
docker exec sofia-postgres psql -U sofia -d sofia_db -c "SELECT version();" 2>&1 | head -1

echo ""
echo "2️⃣ Listando TODOS os schemas..."
docker exec sofia-postgres psql -U sofia -d sofia_db -c "\dn" | head -10

echo ""
echo "3️⃣ Contando tabelas no schema 'public'..."
docker exec sofia-postgres psql -U sofia -d sofia_db -c "
SELECT COUNT(*) as tabelas_no_public
FROM pg_tables
WHERE schemaname = 'public';
"

echo ""
echo "4️⃣ Contando tabelas em TODOS os schemas..."
docker exec sofia-postgres psql -U sofia -d sofia_db -c "
SELECT COUNT(*) as total_tabelas
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
"

echo ""
echo "5️⃣ Listando schemas e contagem de tabelas..."
docker exec sofia-postgres psql -U sofia -d sofia_db -c "
SELECT
  schemaname,
  COUNT(*) as num_tabelas
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname
ORDER BY schemaname;
"

echo ""
echo "6️⃣ Listando todas as tabelas com contagem aproximada..."
docker exec sofia-postgres psql -U sofia -d sofia_db -c "
SELECT
  schemaname,
  relname as tabela,
  n_live_tup as registros
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 20;
"

echo ""
echo "============================================================================"
echo "✅ Verificação concluída!"
echo ""
echo "Se você viu 0 schemas mas o TypeScript encontrou 29 tabelas:"
echo "  → As tabelas podem estar em um schema não-padrão"
echo "  → Execute: bash scripts/investigate.sql para análise completa"
echo "============================================================================"
