#!/usr/bin/env python3
"""
Sofia Pulse - Análise Regional COMPLETA de Papers
Inclui TODAS as tabelas: openalex_papers, arxiv_ai_papers, columnist_papers, person_papers
"""

import psycopg2

# Ler senha do .env
password = 'your_password_here'
try:
    with open('/home/ubuntu/sofia-pulse/.env', 'r') as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                password = line.split('=', 1)[1].strip()
                break
except:
    pass

print("🚀 Sofia Pulse - Análise Regional COMPLETA de Papers")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

print("📡 Conectado ao banco de dados!")
print()

# 1. Verificar quantos papers temos em cada tabela
print("=" * 80)
print("📊 INVENTÁRIO DE PAPERS POR TABELA")
print("=" * 80)
print()

tables_to_check = [
    'openalex_papers',
    'arxiv_ai_papers', 
    'columnist_papers',
    'person_papers',
    'paper_authors',
    'paper_embeddings'
]

for table in tables_to_check:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cursor.fetchone()[0]
        print(f"  {table:<30} {count:>10} registros")
    except Exception as e:
        print(f"  {table:<30} {'ERRO':>10} (tabela não existe ou sem acesso)")

print()

# 2. Verificar estrutura das tabelas para encontrar campos de país/região
print("=" * 80)
print("📋 ESTRUTURA DAS TABELAS (campos relevantes)")
print("=" * 80)
print()

for table in ['openalex_papers', 'arxiv_ai_papers', 'columnist_papers', 'person_papers']:
    try:
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = '{table}'
            AND (column_name LIKE '%country%' OR column_name LIKE '%region%' 
                 OR column_name LIKE '%location%' OR column_name LIKE '%affiliation%'
                 OR column_name LIKE '%institution%' OR column_name LIKE '%university%'
                 OR column_name LIKE '%author%' OR column_name LIKE '%concept%'
                 OR column_name LIKE '%topic%' OR column_name LIKE '%subject%')
            ORDER BY column_name
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"\n{table}:")
            for col, dtype in results:
                print(f"  - {col} ({dtype})")
    except:
        pass

print()
print("=" * 80)
print("✅ INVENTÁRIO CONCLUÍDO")
print("=" * 80)
print()
print("💡 Próximo passo: Analisar cada tabela que tem informação de região/país")
print()

cursor.close()
conn.close()
