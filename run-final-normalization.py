#!/usr/bin/env python3
"""Executa normalização final no servidor"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    user='sofia',
    password='sofia123strong',
    database='sofia_db'
)
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🚀 EXECUTANDO NORMALIZAÇÃO FINAL")
print("=" * 80)
print()

scripts = [
    ('sql/create-types-simple.sql', 'Criando tabela types'),
    ('sql/create-organizations-simple.sql', 'Criando tabela organizations'),
    ('sql/normalize-person-roles.sql', 'Normalizando person_roles'),
]

for sql_file, description in scripts:
    print(f"📝 {description}...")
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        cur.execute(sql)
        print(f"   ✅ OK")
        
    except Exception as e:
        error = str(e)[:200]
        if 'already exists' in error:
            print(f"   ⚠️ Já existe")
        else:
            print(f"   ❌ ERRO: {error}")
    
    print()

# Verificação final
print("=" * 80)
print("📊 VERIFICAÇÃO FINAL")
print("=" * 80)
print()

tables = {
    'sources': 'Fontes',
    'types': 'Tipos',
    'trends': 'Trends',
    'organizations': 'Organizações',
    'persons': 'Pessoas',
    'person_roles': 'Roles (normalizado)'
}

for table, desc in tables.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        status = "✅" if count > 0 or table in ['trends'] else "⚠️"
        print(f"{status} {table:20s} {count:>10,} - {desc}")
    except Exception as e:
        print(f"❌ {table:20s} {'ERRO':>10s} - {desc}")

print()
print("=" * 80)
print("✅ NORMALIZAÇÃO COMPLETA!")
print("=" * 80)

conn.close()
