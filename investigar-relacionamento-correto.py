#!/usr/bin/env python3
"""
Investigar relacionamento CORRETO entre person_papers e universidades
"""

import psycopg2

password = 'your_password_here'
try:
    with open('/home/ubuntu/sofia-pulse/.env', 'r') as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                password = line.split('=', 1)[1].strip()
                break
except:
    pass

print("🔍 Investigando relacionamento person_papers -> person -> university")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# 1. Ver se existe tabela person
print("1. Verificando tabela 'person':")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia' 
    AND table_name LIKE '%person%'
""")
print("Tabelas com 'person':", [row[0] for row in cursor.fetchall()])
print()

# 2. Ver estrutura de person_papers novamente
print("2. Campos em person_papers:")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'sofia' AND table_name = 'person_papers'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  - {row[0]:<30} ({row[1]})")
print()

# 3. Ver um exemplo de person_papers para entender person_id
print("3. Exemplo de person_papers com person_id:")
cursor.execute("""
    SELECT id, person_id, paper_id, paper_source, title
    FROM sofia.person_papers
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  person_id={row[1]}, paper_source={row[3]}, title={row[4][:50]}...")
print()

# 4. Verificar se person_id se relaciona com alguma tabela
print("4. Procurando tabela que tenha 'id' ou 'person_id' para fazer JOIN:")
cursor.execute("""
    SELECT table_name, column_name
    FROM information_schema.columns 
    WHERE table_schema = 'sofia' 
    AND (column_name = 'id' OR column_name = 'person_id' OR column_name LIKE '%university%')
    AND table_name IN (
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'sofia'
    )
    ORDER BY table_name, column_name
""")
results = cursor.fetchall()
tables_with_id = {}
for row in results:
    if row[0] not in tables_with_id:
        tables_with_id[row[0]] = []
    tables_with_id[row[0]].append(row[1])

for table, columns in sorted(tables_with_id.items()):
    print(f"  {table}: {', '.join(columns)}")
print()

# 5. Tentar encontrar como person_id se relaciona
print("5. Verificando se há tabela 'researchers' ou 'authors':")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia' 
    AND (table_name LIKE '%research%' OR table_name LIKE '%author%' OR table_name LIKE '%scientist%')
""")
print("Tabelas relacionadas:", [row[0] for row in cursor.fetchall()])
print()

# 6. Ver paper_source values
print("6. Valores únicos de paper_source:")
cursor.execute("""
    SELECT paper_source, COUNT(*) as count
    FROM sofia.person_papers
    GROUP BY paper_source
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:,} papers")
print()

# 7. Ver se paper_id tem padrão que indica instituição
print("7. Exemplos de paper_id para identificar padrão:")
cursor.execute("""
    SELECT DISTINCT paper_id
    FROM sofia.person_papers
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")
print()

# 8. Verificar se há institution_id em algum lugar
print("8. Procurando campos com 'institution':")
cursor.execute("""
    SELECT table_name, column_name, data_type
    FROM information_schema.columns 
    WHERE table_schema = 'sofia' 
    AND column_name LIKE '%institution%'
""")
for row in cursor.fetchall():
    print(f"  {row[0]}.{row[1]} ({row[2]})")
print()

cursor.close()
conn.close()
