#!/usr/bin/env python3
"""Corrige estrutura de trends e popula person_roles corretamente"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🔧 CORRIGINDO ESTRUTURA E DADOS")
print("=" * 80)
print()

# 1. Verificar e corrigir estrutura de trends
print("1️⃣ Corrigindo tabela trends...")
try:
    # Ver estrutura atual
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='sofia' AND table_name='trends'
        ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    print(f"   Colunas atuais: {', '.join(cols)}")
    
    # Adicionar coluna name se não existir
    if 'name' not in cols:
        print("   ⚠️ Coluna 'name' não existe, adicionando...")
        cur.execute("ALTER TABLE sofia.trends ADD COLUMN name VARCHAR(200)")
        cur.execute("ALTER TABLE sofia.trends ADD COLUMN normalized_name VARCHAR(200)")
        print("   ✅ Colunas adicionadas")
    
except Exception as e:
    print(f"   ❌ Erro: {str(e)[:200]}")

print()

# 2. Verificar se person_patents e person_github_repos existem
print("2️⃣ Verificando tabelas para person_roles...")

tables_exist = {}
for table in ['person_patents', 'person_github_repos', 'person_papers']:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        tables_exist[table] = count
        print(f"   ✅ {table}: {count:,} registros")
    except:
        tables_exist[table] = None
        print(f"   ❌ {table}: NÃO EXISTE")

print()

# 3. Adicionar roles baseado nas tabelas que existem
print("3️⃣ Populando person_roles...")

if tables_exist.get('person_patents'):
    try:
        # Verificar se tipo 'inventor' existe
        cur.execute("SELECT id FROM sofia.types WHERE normalized_name = 'inventor' AND category = 'person_role'")
        inventor_id = cur.fetchone()
        
        if not inventor_id:
            print("   Criando tipo 'inventor'...")
            cur.execute("""
                INSERT INTO sofia.types (name, normalized_name, category, description)
                VALUES ('Inventor', 'inventor', 'person_role', 'Inventor')
                RETURNING id
            """)
            inventor_id = cur.fetchone()[0]
        else:
            inventor_id = inventor_id[0]
        
        cur.execute(f"""
            INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
            SELECT DISTINCT person_id, {inventor_id}, false
            FROM sofia.person_patents
            ON CONFLICT (person_id, role_id) DO NOTHING
        """)
        cur.execute(f"SELECT COUNT(*) FROM sofia.person_roles WHERE role_id = {inventor_id}")
        count = cur.fetchone()[0]
        print(f"   ✅ Inventors: {count:,}")
    except Exception as e:
        print(f"   ❌ Erro inventors: {str(e)[:150]}")

if tables_exist.get('person_github_repos'):
    try:
        # Verificar se tipo 'developer' existe
        cur.execute("SELECT id FROM sofia.types WHERE normalized_name = 'developer' AND category = 'person_role'")
        developer_id = cur.fetchone()
        
        if not developer_id:
            print("   Criando tipo 'developer'...")
            cur.execute("""
                INSERT INTO sofia.types (name, normalized_name, category, description)
                VALUES ('Developer', 'developer', 'person_role', 'Developer')
                RETURNING id
            """)
            developer_id = cur.fetchone()[0]
        else:
            developer_id = developer_id[0]
        
        cur.execute(f"""
            INSERT INTO sofia.person_roles (person_id, role_id, is_primary)
            SELECT DISTINCT person_id, {developer_id}, false
            FROM sofia.person_github_repos
            ON CONFLICT (person_id, role_id) DO NOTHING
        """)
        cur.execute(f"SELECT COUNT(*) FROM sofia.person_roles WHERE role_id = {developer_id}")
        count = cur.fetchone()[0]
        print(f"   ✅ Developers: {count:,}")
    except Exception as e:
        print(f"   ❌ Erro developers: {str(e)[:150]}")

print()

# 4. Verificação final
print("=" * 80)
print("📊 RESULTADO FINAL")
print("=" * 80)
print()

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

conn.close()
