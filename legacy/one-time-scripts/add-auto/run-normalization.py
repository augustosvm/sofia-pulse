#!/usr/bin/env python3
"""Executa normalização completa via Python (sem psql)"""

import os
import psycopg2
from datetime import datetime

print("=" * 80)
print("🚀 NORMALIZAÇÃO COMPLETA DO BANCO SOFIA")
print("=" * 80)
print()

# Conectar ao banco
conn = psycopg2.connect(
    host='localhost',
    port='5432',
    user='sofia',
    password='sofia123strong',
    database='sofia_db'
)
conn.autocommit = False

cur = conn.cursor()

# Contar tabelas antes
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia'")
tables_before = cur.fetchone()[0]

print(f"📊 Tabelas antes: {tables_before}")
print()

# Lista de arquivos SQL para executar
sql_files = [
    'sql/create-sources-table.sql',
    'sql/create-types-table.sql',
    'sql/create-master-tables.sql',
    'sql/expand-persons-table.sql',
    'sql/create-organizations-table.sql',
]

for sql_file in sql_files:
    print(f"🔧 Executando: {sql_file}")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        cur.execute(sql)
        conn.commit()
        print(f"   ✅ OK")
    except Exception as e:
        print(f"   ❌ ERRO: {str(e)[:200]}")
        conn.rollback()
        # Continuar mesmo com erro
    
    print()

# Contar tabelas depois
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia'")
tables_after = cur.fetchone()[0]

print()
print("=" * 80)
print("✅ NORMALIZAÇÃO COMPLETA!")
print("=" * 80)
print()
print(f"📊 Tabelas antes: {tables_before}")
print(f"📊 Tabelas depois: {tables_after}")
print(f"📊 Diferença: {tables_after - tables_before:+d}")
print()

conn.close()
