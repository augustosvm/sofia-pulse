#!/usr/bin/env python3
"""2. Executa consolidação de trends"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("2️⃣ CONSOLIDANDO TRENDS")
print("=" * 80)
print()

# Verificar tabelas de origem
origem = {
    'ai_github_trends': 'GitHub AI trends',
    'stackoverflow_trends': 'StackOverflow trends',
    'tech_job_skill_trends': 'Job skill trends'
}

print("Verificando tabelas de origem:")
total_origem = 0
for table, desc in origem.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        print(f"   {table:30s} {count:>10,} - {desc}")
        total_origem += count
    except:
        print(f"   {table:30s} {'NÃO EXISTE':>10s}")

print(f"\n   TOTAL: {total_origem:,} registros para migrar")
print()

if total_origem == 0:
    print("❌ NENHUMA TABELA DE ORIGEM ENCONTRADA!")
    print("   Trends não podem ser consolidadas sem dados de origem.")
else:
    print("🔧 Migrando dados para trends...")
    
    # Migrar de ai_github_trends
    try:
        cur.execute("""
            INSERT INTO sofia.trends (name, normalized_name, metadata)
            SELECT DISTINCT
                repo_name,
                LOWER(TRIM(repo_name)),
                jsonb_build_object('source', 'ai_github_trends', 'stars', stars)
            FROM sofia.ai_github_trends
            WHERE repo_name IS NOT NULL
            ON CONFLICT (normalized_name) DO NOTHING
        """)
        print("   ✅ ai_github_trends migrado")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)[:150]}")
    
    # Migrar de stackoverflow_trends
    try:
        cur.execute("""
            INSERT INTO sofia.trends (name, normalized_name, metadata)
            SELECT DISTINCT
                tag_name,
                LOWER(TRIM(tag_name)),
                jsonb_build_object('source', 'stackoverflow_trends', 'count', tag_count)
            FROM sofia.stackoverflow_trends
            WHERE tag_name IS NOT NULL
            ON CONFLICT (normalized_name) DO NOTHING
        """)
        print("   ✅ stackoverflow_trends migrado")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)[:150]}")
    
    # Verificar resultado
    cur.execute("SELECT COUNT(*) FROM sofia.trends")
    trends_count = cur.fetchone()[0]
    print(f"\n✅ Trends populada: {trends_count:,} registros")

conn.close()
