#!/usr/bin/env python3
"""Verifica estrutura das tabelas para Skill Gap"""
import os
import sys
from pathlib import Path

# Carregar .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

import psycopg2

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("=" * 60)
print("VERIFICANDO TABELAS PARA SKILL GAP")
print("=" * 60)

# Verificar openalex_papers
print("\n📚 openalex_papers:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'openalex_papers'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]}")

# Contagem e sample de concepts
print("\n📊 Sample de concepts:")
cur.execute("""
    SELECT author_countries, concepts, primary_concept, cited_by_count
    FROM openalex_papers 
    WHERE concepts IS NOT NULL
    LIMIT 3
""")
for row in cur.fetchall():
    print(f"   Countries: {row[0]}")
    print(f"   Concepts: {row[1][:3] if row[1] else None}...")
    print(f"   Primary: {row[2]}")
    print()

# Verificar jobs - tentar várias tabelas
print("\n💼 Buscando tabelas de jobs...")
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema IN ('public', 'sofia')
    AND table_name ILIKE '%job%'
""")
job_tables = cur.fetchall()
print(f"   Tabelas encontradas: {[t[0] for t in job_tables]}")

for table in job_tables:
    print(f"\n   Estrutura de {table[0]}:")
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table[0]}'
        ORDER BY ordinal_position
        LIMIT 15
    """)
    for row in cur.fetchall():
        print(f"      {row[0]}: {row[1]}")

# Contagem de dados
print("\n📈 Contagem de dados:")
cur.execute("SELECT COUNT(*) FROM openalex_papers")
print(f"   openalex_papers: {cur.fetchone()[0]}")

for table in job_tables:
    cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
    print(f"   {table[0]}: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\n✅ Verificação concluída")
