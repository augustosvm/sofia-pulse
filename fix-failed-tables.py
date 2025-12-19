#!/usr/bin/env python3
"""Testa criação de types e organizations individualmente"""

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
print("🔧 CORRIGINDO SCRIPTS QUE FALHARAM")
print("=" * 80)
print()

# 1. Criar tabela types
print("1️⃣ Criando tabela types...")
try:
    with open('sql/create-types-table.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Executar em partes menores
    statements = sql.split(';')
    for i, stmt in enumerate(statements):
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            try:
                cur.execute(stmt)
                if i % 10 == 0:
                    print(f"   Executando statement {i}/{len(statements)}...")
            except Exception as e:
                error_msg = str(e)[:100]
                if 'already exists' in error_msg:
                    print(f"   ⚠️ Já existe: {error_msg}")
                else:
                    print(f"   ❌ Erro: {error_msg}")
    
    # Verificar
    cur.execute("SELECT COUNT(*) FROM sofia.types")
    count = cur.fetchone()[0]
    print(f"   ✅ Tabela types criada: {count} registros")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:200]}")

print()

# 2. Criar tabela organizations
print("2️⃣ Criando tabela organizations...")
try:
    with open('sql/create-organizations-table.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    statements = sql.split(';')
    for i, stmt in enumerate(statements):
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            try:
                cur.execute(stmt)
                if i % 10 == 0:
                    print(f"   Executando statement {i}/{len(statements)}...")
            except Exception as e:
                error_msg = str(e)[:100]
                if 'already exists' in error_msg or 'does not exist' in error_msg:
                    print(f"   ⚠️ {error_msg}")
                else:
                    print(f"   ❌ Erro: {error_msg}")
    
    # Verificar
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    count = cur.fetchone()[0]
    print(f"   ✅ Tabela organizations criada: {count} registros")
    
except Exception as e:
    print(f"   ❌ ERRO: {str(e)[:200]}")

print()

# 3. Verificar resultado final
print("=" * 80)
print("📊 VERIFICAÇÃO FINAL")
print("=" * 80)
print()

tables_to_check = {
    'sources': 'Fontes de dados',
    'types': 'Tipos do sistema',
    'trends': 'Trends/tecnologias',
    'organizations': 'Organizações (PJ)',
    'persons': 'Pessoas (PF)',
    'categories': 'Categorias'
}

for table, desc in tables_to_check.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        status = "✅" if count > 0 or table in ['trends', 'categories'] else "⚠️"
        print(f"{status} {table:20s} {count:>10,} registros - {desc}")
    except Exception as e:
        print(f"❌ {table:20s} {'NÃO EXISTE':>10s} - {desc}")

print()
print("=" * 80)

conn.close()
