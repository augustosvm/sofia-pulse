#!/usr/bin/env python3
"""
ANÁLISE GLOBAL DE TAGS/KEYWORDS
Assuntos mais falados em papers do mundo todo (218K papers)
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

print("🌍 ANÁLISE GLOBAL DE TAGS/KEYWORDS - Papers do Mundo Todo")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# 1. Top 50 keywords globais (todos os papers)
print("=" * 80)
print("TOP 50 ASSUNTOS MAIS FALADOS NO MUNDO (2020-2024)")
print("=" * 80)
print()

cursor.execute("""
SELECT 
    UNNEST(keywords) as keyword,
    COUNT(DISTINCT id) as papers,
    ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / (SELECT COUNT(*) FROM sofia.person_papers WHERE keywords IS NOT NULL AND published_date >= '2020-01-01'), 2) as pct_global
FROM sofia.person_papers
WHERE keywords IS NOT NULL
  AND published_date >= '2020-01-01'
GROUP BY keyword
ORDER BY papers DESC
LIMIT 50
""")

results = cursor.fetchall()
for i, row in enumerate(results, 1):
    print(f"{i:>2}. {row[0]:<50} {row[1]:>8} papers ({row[2]:>5}%)")

print()

# 2. Top 20 keywords de IA/Tech especificamente
print("=" * 80)
print("TOP 20 ASSUNTOS DE IA/TECNOLOGIA")
print("=" * 80)
print()

cursor.execute("""
SELECT 
    UNNEST(keywords) as keyword,
    COUNT(DISTINCT id) as papers,
    ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / (SELECT COUNT(*) FROM sofia.person_papers WHERE keywords IS NOT NULL AND published_date >= '2020-01-01'), 2) as pct_global
FROM sofia.person_papers
WHERE keywords IS NOT NULL
  AND published_date >= '2020-01-01'
  AND (
    keywords::text ILIKE '%artificial intelligence%' OR
    keywords::text ILIKE '%machine learning%' OR
    keywords::text ILIKE '%deep learning%' OR
    keywords::text ILIKE '%computer%' OR
    keywords::text ILIKE '%neural%' OR
    keywords::text ILIKE '%quantum%' OR
    keywords::text ILIKE '%blockchain%' OR
    keywords::text ILIKE '%data%' OR
    keywords::text ILIKE '%algorithm%' OR
    keywords::text ILIKE '%software%'
  )
GROUP BY keyword
ORDER BY papers DESC
LIMIT 20
""")

results = cursor.fetchall()
for i, row in enumerate(results, 1):
    print(f"{i:>2}. {row[0]:<50} {row[1]:>8} papers ({row[2]:>5}%)")

print()

# 3. Categorias principais (agrupadas)
print("=" * 80)
print("CATEGORIAS PRINCIPAIS (agrupadas)")
print("=" * 80)
print()

categories = {
    'Medicine & Health': ['Medicine', 'COVID-19', 'SARS-CoV-2', 'Coronavirus', 'Health', 'Disease', 'Clinical', 'Patient', 'Medical'],
    'Computer Science & AI': ['Computer science', 'Artificial intelligence', 'Machine learning', 'Deep learning', 'Algorithm', 'Software', 'Data'],
    'Physics & Astronomy': ['Physics', 'Astrophysics', 'Quantum', 'Particle', 'Cosmology', 'Astronomy'],
    'Biology & Life Sciences': ['Biology', 'Genetics', 'Genome', 'Protein', 'Cell', 'Molecular', 'DNA'],
    'Materials Science': ['Materials science', 'Graphene', 'Semiconductor', 'Nanotechnology', 'Crystal'],
    'Climate & Environment': ['Climate change', 'Global warming', 'Environmental science', 'Ecology', 'Sustainability'],
    'Engineering': ['Engineering', 'Mechanical engineering', 'Electrical engineering', 'Civil engineering']
}

for category, keywords in categories.items():
    conditions = " OR ".join([f"keywords::text ILIKE '%{kw}%'" for kw in keywords])
    
    cursor.execute(f"""
        SELECT COUNT(DISTINCT id) as papers
        FROM sofia.person_papers
        WHERE keywords IS NOT NULL
          AND published_date >= '2020-01-01'
          AND ({conditions})
    """)
    
    count = cursor.fetchone()[0]
    pct = count * 100.0 / 218026  # Total de papers com país
    print(f"{category:<30} {count:>8} papers ({pct:>5.2f}%)")

print()
print("=" * 80)
print("✅ ANÁLISE GLOBAL CONCLUÍDA")
print("=" * 80)
print()
print("Total de papers analisados: 218.026 (2020-2024)")
print("Fonte: person_papers (keywords)")
print()

cursor.close()
conn.close()
