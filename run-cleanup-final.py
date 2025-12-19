#!/usr/bin/env python3
"""Executa limpeza final e valida estado do banco"""

import psycopg2
import os

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🧹 LIMPEZA FINAL DO BANCO DE DADOS")
print("=" * 80)
print()

# 1. Listar tabelas ANTES
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia'")
count_before = cur.fetchone()[0]
print(f"Total de tabelas ANTES: {count_before}")

# 2. Ler e executar SQL
sql_file = 'cleanup-obsolete-tables.sql'
if not os.path.exists(sql_file):
    print(f"❌ SQL file not found: {sql_file}")
    exit(1)
    
with open(sql_file, 'r') as f:
    sql_content = f.read()

print(f"Executando {sql_file}...")
try:
    cur.execute(sql_content)
    print("✅ SQL executado com sucesso!")
except Exception as e:
    print(f"❌ Erro na execução SQL: {e}")

print()

# 3. Listar tabelas DEPOIS
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia'")
count_after = cur.fetchone()[0]
print(f"Total de tabelas DEPOIS: {count_after}")
print(f"📉 Redução: {count_before - count_after} tabelas removidas")

print()
print("📊 Estado Final das Tabelas Críticas:")
critical_tables = ['trends', 'organizations', 'persons', 'person_roles']
for t in critical_tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{t}")
        c = cur.fetchone()[0]
        print(f"   - {t:15s}: {c:,} registros")
    except:
        print(f"   - {t:15s}: [REMOVIDA/ERRO]")

conn.close()
