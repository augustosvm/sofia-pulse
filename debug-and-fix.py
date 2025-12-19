#!/usr/bin/env python3
"""Investiga erros na criação de organizations e person_roles"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🔍 INVESTIGANDO ERROS")
print("=" * 80)
print()

# 1. Verificar se institutions existe
print("1️⃣ Verificando tabela institutions...")
try:
    cur.execute("SELECT COUNT(*) FROM sofia.institutions")
    count = cur.fetchone()[0]
    print(f"   ✅ institutions existe: {count:,} registros")
except Exception as e:
    print(f"   ❌ institutions NÃO existe: {str(e)[:100]}")

print()

# 2. Tentar criar organizations manualmente
print("2️⃣ Criando organizations manualmente...")
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sofia.organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            normalized_name VARCHAR(500) UNIQUE NOT NULL,
            type VARCHAR(100),
            source_id INTEGER,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    print("   ✅ Tabela organizations criada")
    
    # Popular com dados básicos
    cur.execute("""
        INSERT INTO sofia.organizations (name, normalized_name, type)
        SELECT DISTINCT
            institution,
            LOWER(TRIM(institution)),
            'research_center'
        FROM sofia.brazil_research_institutions
        WHERE institution IS NOT NULL
        LIMIT 100
        ON CONFLICT (normalized_name) DO NOTHING
    """)
    
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    count = cur.fetchone()[0]
    print(f"   ✅ Populada: {count:,} registros")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:200]}")

print()

# 3. Tentar criar person_roles manualmente
print("3️⃣ Criando person_roles manualmente...")
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sofia.person_roles (
            id SERIAL PRIMARY KEY,
            person_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            is_primary BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(person_id, role_id)
        )
    """)
    print("   ✅ Tabela person_roles criada")
    
    cur.execute("SELECT COUNT(*) FROM sofia.person_roles")
    count = cur.fetchone()[0]
    print(f"   ✅ Registros: {count:,}")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:200]}")

print()

# 4. Verificação final
print("=" * 80)
print("📊 RESULTADO")
print("=" * 80)
print()

for table in ['sources', 'types', 'trends', 'organizations', 'persons', 'person_roles']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM sofia.{table}')
        count = cur.fetchone()[0]
        print(f'✅ {table:20s} {count:>10,}')
    except:
        print(f'❌ {table:20s} {"NÃO EXISTE":>10s}')

conn.close()
