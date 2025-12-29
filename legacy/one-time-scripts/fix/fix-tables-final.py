#!/usr/bin/env python3
"""Executa criação de types e organizations - versão corrigida"""

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
print("🔧 CORRIGINDO TABELAS TYPES E ORGANIZATIONS")
print("=" * 80)
print()

# 1. Criar types
print("1️⃣ Criando tabela types...")
try:
    with open('sql/create-types-simple.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    cur.execute(sql)
    
    cur.execute("SELECT COUNT(*) FROM sofia.types")
    count = cur.fetchone()[0]
    print(f"   ✅ Tabela types criada: {count} tipos")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:300]}")

print()

# 2. Criar organizations
print("2️⃣ Criando tabela organizations...")
try:
    with open('sql/create-organizations-simple.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    cur.execute(sql)
    
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    count = cur.fetchone()[0]
    print(f"   ✅ Tabela organizations criada: {count:,} organizações")
    
    # Mostrar distribuição por tipo
    cur.execute("""
        SELECT type, COUNT(*) as count 
        FROM sofia.organizations 
        GROUP BY type 
        ORDER BY count DESC 
        LIMIT 5
    """)
    print("   Distribuição por tipo:")
    for row in cur.fetchall():
        print(f"      {row[0]:20s} {row[1]:>10,}")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:300]}")

print()

# 3. Verificação final
print("=" * 80)
print("📊 VERIFICAÇÃO FINAL")
print("=" * 80)
print()

tables = {
    'sources': 'Fontes de dados',
    'types': 'Tipos do sistema',
    'trends': 'Trends/tecnologias',
    'organizations': 'Organizações (PJ)',
    'persons': 'Pessoas (PF)'
}

for table, desc in tables.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        status = "✅" if count > 0 or table == 'trends' else "⚠️"
        print(f"{status} {table:20s} {count:>10,} - {desc}")
    except Exception as e:
        print(f"❌ {table:20s} {'ERRO':>10s} - {desc}")

print()
print("=" * 80)
print("✅ CORREÇÃO COMPLETA!")
print("=" * 80)

conn.close()
