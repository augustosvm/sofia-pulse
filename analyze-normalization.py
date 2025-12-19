#!/usr/bin/env python3
"""Verifica tabelas criadas e identifica obsoletas"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    user='sofia',
    password='sofia123strong',
    database='sofia_db'
)

cur = conn.cursor()

print("=" * 80)
print("📊 ANÁLISE PÓS-NORMALIZAÇÃO")
print("=" * 80)
print()

# 1. Tabelas Master Criadas
print("✅ TABELAS MASTER CRIADAS:")
print()

master_tables = ['sources', 'types', 'trends', 'organizations', 'persons', 'categories']

for table in master_tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        print(f"   {table:30s} {count:>15,} registros")
    except Exception as e:
        print(f"   {table:30s} {'NÃO EXISTE':>15s}")

print()

# 2. Tabelas Antigas/Obsoletas
print("⚠️  TABELAS POTENCIALMENTE OBSOLETAS:")
print()

# Tabelas que foram substituídas
obsolete_candidates = {
    'companies': 'Substituída por organizations',
    'institutions': 'Renomeada para organizations',
    'authors': 'Dados migrados para persons',
    'ai_github_trends': 'Consolidada em tech_trends',
    'stackoverflow_trends': 'Consolidada em tech_trends',
    'hackernews_stories': 'Consolidada em community_posts',
    'hacker_news_stories': 'Duplicata de hackernews_stories',
    'reddit_tech': 'Consolidada em community_posts',
    'reddit_tech_posts': 'Consolidada em community_posts',
    'epo_patents': 'Consolidada em patents',
    'wipo_china_patents': 'Consolidada em patents',
    'person_patents': 'Consolidada em patents',
    'columnist_insights': 'Vazia, não usada',
    'tech_embedding_jobs': 'Duplicata vazia',
    'embedding_jobs': 'Duplicata vazia',
    'countries_normalization': 'Temporária, não mais usada',
}

obsolete_found = []

for table, reason in obsolete_candidates.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        
        # Verificar se tem FKs apontando para ela
        cur.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_schema = 'sofia'
            AND ccu.table_name = '{table}'
        """)
        fk_count = cur.fetchone()[0]
        
        status = "⚠️ TEM FKs" if fk_count > 0 else "✅ Seguro"
        print(f"   {table:35s} {count:>10,} regs  {status:12s}  {reason}")
        
        if fk_count == 0:
            obsolete_found.append(table)
            
    except Exception:
        pass  # Tabela não existe

print()

# 3. Tabelas com colunas VARCHAR que deveriam ser FK
print("🔧 COLUNAS VARCHAR QUE DEVERIAM SER FK:")
print()

# tech_trends
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(trend_id) as with_fk,
        COUNT(*) - COUNT(trend_id) as missing_fk
    FROM sofia.tech_trends
""")
row = cur.fetchone()
if row[2] > 0:
    print(f"   tech_trends.trend_id: {row[2]:,} registros sem FK")

# community_posts
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(person_id) as with_fk,
        COUNT(*) - COUNT(person_id) as missing_fk
    FROM sofia.community_posts
""")
row = cur.fetchone()
if row[2] > 0:
    print(f"   community_posts.person_id: {row[2]:,} registros sem FK")

# organizations
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(type_id) as with_fk,
        COUNT(*) - COUNT(type_id) as missing_fk
    FROM sofia.organizations
""")
row = cur.fetchone()
if row[2] > 0:
    print(f"   organizations.type_id: {row[2]:,} registros sem FK")

print()

# 4. Gerar script de limpeza
print("=" * 80)
print("📝 GERANDO SCRIPT DE LIMPEZA...")
print("=" * 80)
print()

cleanup_sql = """-- ============================================================
-- LIMPEZA DE TABELAS OBSOLETAS
-- Gerado automaticamente após normalização
-- ============================================================

-- ATENÇÃO: Execute apenas após validar que os dados foram migrados!

BEGIN;

"""

for table in sorted(obsolete_found):
    cleanup_sql += f"-- Remover {table}\n"
    cleanup_sql += f"DROP TABLE IF EXISTS sofia.{table} CASCADE;\n\n"

cleanup_sql += """
COMMIT;

-- Verificar tabelas restantes
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema='sofia' AND table_name=t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'sofia'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
"""

with open('sql/cleanup-obsolete-tables.sql', 'w', encoding='utf-8') as f:
    f.write(cleanup_sql)

print(f"✅ Script criado: sql/cleanup-obsolete-tables.sql")
print(f"   Tabelas a remover: {len(obsolete_found)}")
print()

for table in sorted(obsolete_found):
    print(f"   - {table}")

print()
print("=" * 80)
print("✅ ANÁLISE COMPLETA!")
print("=" * 80)

conn.close()
