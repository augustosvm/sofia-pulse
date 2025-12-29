#!/usr/bin/env python3
"""
Sofia Pulse - Análise Regional por TAGS/KEYWORDS de IA
Focando em: AI, ML, Computer Vision, Quantum, Climate AI, LLMs, etc.
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

print("🚀 Sofia Pulse - Análise Regional por TAGS/KEYWORDS de IA")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

print("📡 Conectado ao banco de dados!")
print()

# Definir categorias de IA
ai_categories = {
    'Artificial Intelligence': ['Artificial intelligence', 'AI'],
    'Machine Learning': ['Machine learning', 'Deep learning', 'Neural network', 'Convolutional neural network'],
    'Computer Vision': ['Computer vision', 'Image processing', 'Pattern recognition'],
    'Natural Language Processing': ['Natural language processing', 'NLP', 'Language model'],
    'Quantum Computing': ['Quantum', 'Quantum computing', 'Quantum chemistry', 'Qubit', 'Superconducting quantum'],
    'Climate AI': ['Climate change', 'Global warming', 'Environmental science', 'Climatology'],
    'Blockchain': ['Blockchain', 'Cryptocurrency', 'Bitcoin']
}

print("=" * 80)
print("📊 PAPERS POR CATEGORIA DE IA (Global)")
print("=" * 80)
print()

for category, keywords in ai_categories.items():
    # Criar condição SQL para buscar qualquer keyword da categoria
    conditions = " OR ".join([f"keywords::text ILIKE '%{kw}%'" for kw in keywords])
    
    cursor.execute(f"""
        SELECT COUNT(DISTINCT id) as count
        FROM sofia.person_papers
        WHERE keywords IS NOT NULL
          AND ({conditions})
    """)
    
    count = cursor.fetchone()[0]
    print(f"{category:<35} {count:>8} papers")

print()

# Análise por país para cada categoria
print("=" * 80)
print("📊 TOP 5 PAÍSES POR CATEGORIA DE IA")
print("=" * 80)
print()

for category, keywords in ai_categories.items():
    print(f"\n{category}:")
    print("-" * 80)
    
    conditions = " OR ".join([f"pp.keywords::text ILIKE '%{kw}%'" for kw in keywords])
    
    cursor.execute(f"""
        WITH ai_papers AS (
            SELECT pp.id, gu.country_code
            FROM sofia.person_papers pp
            JOIN sofia.global_universities_progress gu 
              ON pp.paper_source = 'global_university'
            WHERE pp.keywords IS NOT NULL
              AND ({conditions})
              AND gu.country_code IS NOT NULL
            
            UNION ALL
            
            SELECT pp.id, 'BR' as country_code
            FROM sofia.person_papers pp
            WHERE pp.paper_source = 'brazilian_university'
              AND pp.keywords IS NOT NULL
              AND ({conditions})
        )
        SELECT 
            country_code,
            COUNT(DISTINCT id) as papers,
            ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (), 2) as pct
        FROM ai_papers
        GROUP BY country_code
        ORDER BY papers DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]:<5} {row[1]:>6} papers ({row[2]:>5}%)")

print()
print("=" * 80)
print("✅ ANÁLISE POR TAGS/KEYWORDS CONCLUÍDA")
print("=" * 80)
print()
print("💡 Agora temos dados específicos de IA por região!")
print()

cursor.close()
conn.close()
