#!/usr/bin/env python3
"""Popula organizations e person_roles com dados existentes"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("📦 POPULANDO TABELAS NORMALIZADAS")
print("=" * 80)
print()

# 1. Popular organizations com research institutions
print("1️⃣ Populando organizations...")
try:
    # De brazil_research_institutions
    cur.execute("""
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        SELECT DISTINCT
            institution,
            LOWER(TRIM(REGEXP_REPLACE(institution, '\s+', ' ', 'g'))),
            CASE 
                WHEN institution ILIKE '%university%' OR institution ILIKE '%universidade%' THEN 'university'
                WHEN institution ILIKE '%hospital%' THEN 'hospital'
                WHEN institution ILIKE '%school%' OR institution ILIKE '%escola%' THEN 'school'
                ELSE 'research_center'
            END,
            jsonb_build_object('source', 'brazil_research_institutions')
        FROM sofia.brazil_research_institutions
        WHERE institution IS NOT NULL
        ON CONFLICT (normalized_name) DO NOTHING
    """)
    
    # De global_research_institutions
    cur.execute("""
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        SELECT DISTINCT
            institution,
            LOWER(TRIM(REGEXP_REPLACE(institution, '\s+', ' ', 'g'))),
            CASE 
                WHEN institution ILIKE '%university%' THEN 'university'
                WHEN institution ILIKE '%hospital%' THEN 'hospital'
                WHEN institution ILIKE '%school%' THEN 'school'
                WHEN institution ILIKE '%lab%' THEN 'laboratory'
                ELSE 'research_center'
            END,
            jsonb_build_object('source', 'global_research_institutions')
        FROM sofia.global_research_institutions
        WHERE institution IS NOT NULL
        ON CONFLICT (normalized_name) DO NOTHING
    """)
    
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    count = cur.fetchone()[0]
    print(f"   ✅ Organizations: {count:,} registros")
    
    # Distribuição por tipo
    cur.execute("""
        SELECT type, COUNT(*) 
        FROM sofia.organizations 
        GROUP BY type 
        ORDER BY COUNT(*) DESC
    """)
    print("   Distribuição:")
    for row in cur.fetchall():
        print(f"      {row[0]:20s} {row[1]:>10,}")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:300]}")

print()

# 2. Popular person_roles de persons que têm roles
print("2️⃣ Populando person_roles...")
try:
    # Adicionar roles básicos aos types se não existirem
    cur.execute("""
        INSERT INTO sofia.types (name, normalized_name, category, description, display_order)
        VALUES 
            ('Researcher', 'researcher', 'person_role', 'Pesquisador', 10),
            ('Inventor', 'inventor', 'person_role', 'Inventor', 20),
            ('Developer', 'developer', 'person_role', 'Desenvolvedor', 30)
        ON CONFLICT (normalized_name) DO NOTHING
    """)
    
    # Migrar roles de persons para person_roles
    # Pessoas com papers = researchers
    cur.execute("""
        INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
        SELECT DISTINCT
            p.id,
            (SELECT id FROM sofia.types WHERE normalized_name = 'researcher' AND category = 'person_role' LIMIT 1),
            true
        FROM sofia.persons p
        WHERE EXISTS (
            SELECT 1 FROM sofia.person_papers pp WHERE pp.person_id = p.id
        )
        ON CONFLICT (person_id, role_id) DO NOTHING
    """)
    
    # Pessoas com patents = inventors
    cur.execute("""
        INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
        SELECT DISTINCT
            p.id,
            (SELECT id FROM sofia.types WHERE normalized_name = 'inventor' AND category = 'person_role' LIMIT 1),
            false
        FROM sofia.persons p
        WHERE EXISTS (
            SELECT 1 FROM sofia.person_patents pp WHERE pp.person_id = p.id
        )
        ON CONFLICT (person_id, role_id) DO NOTHING
    """)
    
    # Pessoas com github repos = developers
    cur.execute("""
        INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
        SELECT DISTINCT
            p.id,
            (SELECT id FROM sofia.types WHERE normalized_name = 'developer' AND category = 'person_role' LIMIT 1),
            false
        FROM sofia.persons p
        WHERE EXISTS (
            SELECT 1 FROM sofia.person_github_repos pgr WHERE pgr.person_id = p.id
        )
        ON CONFLICT (person_id, role_id) DO NOTHING
    """)
    
    cur.execute("SELECT COUNT(*) FROM sofia.person_roles")
    count = cur.fetchone()[0]
    print(f"   ✅ Person_roles: {count:,} registros")
    
    # Distribuição
    cur.execute("""
        SELECT t.name, COUNT(*) 
        FROM sofia.person_roles pr
        JOIN sofia.types t ON pr.role_id = t.id
        GROUP BY t.name
        ORDER BY COUNT(*) DESC
    """)
    print("   Distribuição:")
    for row in cur.fetchall():
        print(f"      {row[0]:20s} {row[1]:>10,}")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:300]}")

print()

# 3. Verificação final
print("=" * 80)
print("📊 RESULTADO FINAL")
print("=" * 80)
print()

tables = {
    'sources': 'Fontes de dados',
    'types': 'Tipos do sistema',
    'trends': 'Tecnologias/trends',
    'organizations': 'Organizações (PJ)',
    'persons': 'Pessoas (PF)',
    'person_roles': 'Roles normalizados'
}

for table, desc in tables.items():
    try:
        cur.execute(f'SELECT COUNT(*) FROM sofia.{table}')
        count = cur.fetchone()[0]
        status = "✅" if count > 0 or table == 'trends' else "⚠️"
        print(f'{status} {table:20s} {count:>10,} - {desc}')
    except:
        print(f'❌ {table:20s} {"ERRO":>10s} - {desc}')

print()
print("=" * 80)
print("✅ NORMALIZAÇÃO COMPLETA E POPULADA!")
print("=" * 80)

conn.close()
