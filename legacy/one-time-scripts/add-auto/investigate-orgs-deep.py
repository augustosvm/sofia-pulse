#!/usr/bin/env python3
"""Investigação profunda da tabela organizations"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 INVESTIGANDO ORGANIZATIONS (404 vs 400k)")
print("=" * 80)
print()

# 1. Verificar tabela antiga 'institutions'
print("1️⃣ STATUS DAS TABELAS FONTE:")
sources = ['institutions', 'brazil_research_institutions', 'global_research_institutions']

for table in sources:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        print(f"   ✅ {table}: {count:,} registros")
        
        # Se tiver dados, mostrar amostra
        if count > 0:
            cur.execute(f"SELECT * FROM sofia.{table} LIMIT 1")
            col_names = [desc[0] for desc in cur.description]
            print(f"      Colunas: {', '.join(col_names)}")
            
    except Exception as e:
        print(f"   ❌ {table}: NÃO ENCONTRADA ou ERRO ({e})")

print()

# 2. Verificar Organizations atual
print("2️⃣ STATUS Tabela 'organizations':")
cur.execute("SELECT COUNT(*) FROM sofia.organizations")
count = cur.fetchone()[0]
print(f"   Total atual: {count:,}")

# Verificar distribuição atual
cur.execute("SELECT type, COUNT(*) FROM sofia.organizations GROUP BY type")
print("   Distribuição atual:")
for r in cur.fetchall():
    print(f"      - {r[0]}: {r[1]:,}")

print()

# 3. Teste de Migração Manual
print("3️⃣ TESTE DE MIGRAÇÃO (Diagnóstico de Erro):")

# Tentar inserir 1000 registros que sabemos que existem e ver se falha
try:
    print("   Tentando migrar 1000 registros de brazil_research_institutions...")
    cur.execute("""
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        SELECT 
            institution, 
            LOWER(TRIM(institution)), 
            'research_center',
            '{"source": "test_migration"}'::jsonb
        FROM sofia.brazil_research_institutions 
        WHERE institution IS NOT NULL
        LIMIT 1000
        ON CONFLICT (normalized_name) DO NOTHING
    """)
    # Precisamos do commit aqui para contar de verdade, pois o script usa autocommit na conexão,
    # mas o cursor pode estar em transação implicita dependendo do driver.
    # No autocommit=True do psycopg2, cada execute é commitado.
    
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    new_count = cur.fetchone()[0]
    print(f"   ✅ Sucesso parcial? Novo total: {new_count:,} (+{new_count - count})")
    
except Exception as e:
    print(f"   ❌ ERRO NA MIGRAÇÃO: {e}")

print()
print("=" * 80)
conn.close()
