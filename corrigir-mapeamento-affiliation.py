#!/usr/bin/env python3
"""
CORRIGIR MAPEAMENTO: Usar primary_affiliation para identificar país/região
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

print("🔧 CORRIGINDO MAPEAMENTO - Usando primary_affiliation")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# 1. Ver top affiliations
print("1. Top 20 affiliations em persons:")
cursor.execute("""
    SELECT primary_affiliation, COUNT(*) as count
    FROM sofia.persons
    WHERE primary_affiliation IS NOT NULL
    GROUP BY primary_affiliation
    ORDER BY count DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<50} {row[1]:>6} persons")
print()

# 2. Verificar se há tabela dim_university ou brazil_research_institutions
print("2. Verificando mapeamento de universidades:")
cursor.execute("""
    SELECT university_code, university_name, country_id
    FROM sofia.dim_university
    LIMIT 10
""")
print("Exemplos de dim_university:")
for row in cursor.fetchall():
    print(f"  {row[0]:<20} {row[1]:<50} country_id={row[2]}")
print()

# 3. Verificar brazil_research_institutions
cursor.execute("""
    SELECT institution, COUNT(*) as count
    FROM sofia.brazil_research_institutions
    GROUP BY institution
    ORDER BY count DESC
    LIMIT 10
""")
print("Top instituições brasileiras:")
for row in cursor.fetchall():
    print(f"  {row[0]:<50} {row[1]:>6}")
print()

# 4. Verificar global_research_institutions
cursor.execute("""
    SELECT institution_country, COUNT(*) as count
    FROM sofia.global_research_institutions
    WHERE institution_country IS NOT NULL
    GROUP BY institution_country
    ORDER BY count DESC
    LIMIT 10
""")
print("Top países em global_research_institutions:")
for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]:>6} instituições")
print()

# 5. Tentar fazer JOIN com global_research_institutions
print("5. Testando JOIN persons -> global_research_institutions:")
cursor.execute("""
    SELECT 
        gri.institution_country,
        COUNT(DISTINCT p.id) as persons_count,
        COUNT(DISTINCT pp.id) as papers_count
    FROM sofia.persons p
    LEFT JOIN sofia.global_research_institutions gri 
      ON p.primary_affiliation = gri.institution
    LEFT JOIN sofia.person_papers pp ON p.id = pp.person_id
    WHERE gri.institution_country IS NOT NULL
    GROUP BY gri.institution_country
    ORDER BY papers_count DESC
    LIMIT 10
""")
print("Papers por país (via global_research_institutions):")
for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]:>6} persons, {row[2]:>8} papers")
print()

cursor.close()
conn.close()
