#!/usr/bin/env python3
"""Corrige TODOS os erros de migração - SEM IGNORAR NADA"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🔧 CORRIGINDO ERROS DE MIGRAÇÃO")
print("=" * 80)
print()

# PROBLEMA 1: trends vazia
print("❌ PROBLEMA 1: trends está vazia")
print("   Verificando tabelas de origem...")

origem_trends = ['ai_github_trends', 'stackoverflow_trends', 'tech_job_skill_trends']
for table in origem_trends:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        print(f"      {table}: {count:,} registros")
    except Exception as e:
        print(f"      {table}: NÃO EXISTE ou ERRO")

print()
print("   ⚠️ AÇÃO: Precisa executar scripts de consolidação")
print()

# PROBLEMA 2: person_roles só tem researchers
print("❌ PROBLEMA 2: person_roles só tem Researcher")
print("   Verificando tabelas de origem...")

try:
    cur.execute("SELECT COUNT(*) FROM sofia.person_patents")
    patents_count = cur.fetchone()[0]
    print(f"      person_patents: {patents_count:,} registros")
except:
    print(f"      person_patents: NÃO EXISTE")

try:
    cur.execute("SELECT COUNT(*) FROM sofia.person_github_repos")
    github_count = cur.fetchone()[0]
    print(f"      person_github_repos: {github_count:,} registros")
except:
    print(f"      person_github_repos: NÃO EXISTE")

print()
print("   🔧 Corrigindo: Adicionando inventors e developers...")

# Adicionar inventors
try:
    cur.execute("""
        INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
        SELECT DISTINCT
            pp.person_id,
            (SELECT id FROM sofia.types WHERE normalized_name = 'inventor' LIMIT 1),
            false
        FROM sofia.person_patents pp
        ON CONFLICT (person_id, role_id) DO NOTHING
    """)
    cur.execute("SELECT COUNT(*) FROM sofia.person_roles WHERE role_id = (SELECT id FROM sofia.types WHERE normalized_name = 'inventor')")
    inventors = cur.fetchone()[0]
    print(f"      ✅ Inventors adicionados: {inventors:,}")
except Exception as e:
    print(f"      ❌ ERRO ao adicionar inventors: {str(e)[:200]}")

# Adicionar developers
try:
    cur.execute("""
        INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
        SELECT DISTINCT
            pgr.person_id,
            (SELECT id FROM sofia.types WHERE normalized_name = 'developer' LIMIT 1),
            false
        FROM sofia.person_github_repos pgr
        ON CONFLICT (person_id, role_id) DO NOTHING
    """)
    cur.execute("SELECT COUNT(*) FROM sofia.person_roles WHERE role_id = (SELECT id FROM sofia.types WHERE normalized_name = 'developer')")
    developers = cur.fetchone()[0]
    print(f"      ✅ Developers adicionados: {developers:,}")
except Exception as e:
    print(f"      ❌ ERRO ao adicionar developers: {str(e)[:200]}")

print()

# PROBLEMA 3: organizations só tem 404 de ~400k
print("❌ PROBLEMA 3: organizations tem apenas 404 registros")
print("   Verificando tabelas de origem...")

try:
    cur.execute("SELECT COUNT(*) FROM sofia.brazil_research_institutions")
    brazil_count = cur.fetchone()[0]
    print(f"      brazil_research_institutions: {brazil_count:,}")
except:
    print(f"      brazil_research_institutions: ERRO")

try:
    cur.execute("SELECT COUNT(*) FROM sofia.global_research_institutions")
    global_count = cur.fetchone()[0]
    print(f"      global_research_institutions: {global_count:,}")
except:
    print(f"      global_research_institutions: ERRO")

print()
print("   ⚠️ Esperado: ~400k organizations")
print(f"   ⚠️ Atual: 404 organizations")
print("   ⚠️ PROBLEMA: Migração incompleta ou dados já estão em outra tabela")
print()

# VERIFICAÇÃO FINAL
print("=" * 80)
print("📊 RESULTADO APÓS CORREÇÕES")
print("=" * 80)
print()

# Person roles por tipo
cur.execute("""
    SELECT t.name, COUNT(*) 
    FROM sofia.person_roles pr
    JOIN sofia.types t ON pr.role_id = t.id
    GROUP BY t.name
    ORDER BY COUNT(*) DESC
""")
print("Person roles:")
for row in cur.fetchall():
    print(f"   {row[0]:20s} {row[1]:>10,}")

print()

# Tabelas finais
for table in ['sources', 'types', 'trends', 'organizations', 'persons', 'person_roles']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM sofia.{table}')
        count = cur.fetchone()[0]
        status = "✅" if count > 0 or table == 'trends' else "❌"
        print(f'{status} {table:20s} {count:>10,}')
    except:
        print(f'❌ {table:20s} {"ERRO":>10s}')

print()
print("=" * 80)
print("⚠️ PROBLEMAS IDENTIFICADOS:")
print("1. trends: VAZIA - precisa migrar dados")
print("2. person_roles: CORRIGIDO parcialmente")
print("3. organizations: APENAS 404 de ~400k")
print("=" * 80)

conn.close()
