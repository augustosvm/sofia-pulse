#!/usr/bin/env python3
"""
Verificar campos de tags/keywords nos papers
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

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

print("🔍 Verificando campos de tags/keywords")
print("=" * 80)
print()

# 1. Ver estrutura completa de person_papers
print("1. Campos disponíveis em person_papers:")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'sofia' AND table_name = 'person_papers'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  - {row[0]:<30} ({row[1]})")

print()

# 2. Ver exemplo de keywords
print("2. Exemplo de keywords em person_papers:")
cursor.execute("""
    SELECT keywords 
    FROM sofia.person_papers 
    WHERE keywords IS NOT NULL 
    LIMIT 5
""")
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"  {i}. {row[0]}")

print()

# 3. Top keywords relacionados a IA
print("3. Top keywords relacionados a IA/Tech:")
cursor.execute("""
    SELECT UNNEST(keywords) as keyword, COUNT(*) as count
    FROM sofia.person_papers
    WHERE keywords IS NOT NULL
      AND (
        keywords::text ILIKE '%artificial intelligence%' OR
        keywords::text ILIKE '%machine learning%' OR
        keywords::text ILIKE '%deep learning%' OR
        keywords::text ILIKE '%neural network%' OR
        keywords::text ILIKE '%computer vision%' OR
        keywords::text ILIKE '%natural language%' OR
        keywords::text ILIKE '%quantum%' OR
        keywords::text ILIKE '%blockchain%' OR
        keywords::text ILIKE '%climate%'
      )
    GROUP BY keyword
    ORDER BY count DESC
    LIMIT 20
""")
results = cursor.fetchall()
if results:
    for row in results:
        print(f"  {row[0]:<50} {row[1]:>6} papers")
else:
    print("  Nenhum resultado encontrado")

print()

# 4. Verificar openalex_papers
print("4. Campos em openalex_papers:")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema IN ('public', 'sofia') AND table_name = 'openalex_papers'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  - {row[0]:<30} ({row[1]})")

print()

# 5. Top concepts em openalex_papers
print("5. Top concepts em openalex_papers:")
cursor.execute("""
    SELECT UNNEST(concepts) as concept, COUNT(*) as count
    FROM openalex_papers
    WHERE concepts IS NOT NULL
    GROUP BY concept
    ORDER BY count DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<50} {row[1]:>6} papers")

cursor.close()
conn.close()
