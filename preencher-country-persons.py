#!/usr/bin/env python3
"""
Script para PREENCHER campo country na tabela persons
Usando mapeamento: primary_affiliation -> global_research_institutions.institution_country
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

print("🔧 PREENCHENDO CAMPO COUNTRY EM PERSONS")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# 1. Verificar situação atual
print("1. Situação ANTES da correção:")
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN country IS NOT NULL AND country != '' THEN 1 END) as with_country
    FROM sofia.persons
""")
row = cursor.fetchone()
print(f"  Total persons: {row[0]:,}")
print(f"  Com country: {row[1]:,} ({row[1]*100.0/row[0]:.1f}%)")
print()

# 2. Atualizar country usando global_research_institutions
print("2. Atualizando country usando global_research_institutions...")
cursor.execute("""
    UPDATE sofia.persons p
    SET country = gri.institution_country
    FROM sofia.global_research_institutions gri
    WHERE p.primary_affiliation = gri.institution
      AND gri.institution_country IS NOT NULL
      AND (p.country IS NULL OR p.country = '')
""")
updated_global = cursor.rowcount
print(f"  ✅ Atualizados {updated_global:,} registros via global_research_institutions")
conn.commit()

# 3. Atualizar country para Brasil (affiliations brasileiras)
print("3. Atualizando country='BR' para instituições brasileiras...")
cursor.execute("""
    UPDATE sofia.persons
    SET country = 'BR'
    WHERE (country IS NULL OR country = '')
      AND primary_affiliation IN (
        SELECT DISTINCT institution 
        FROM sofia.brazil_research_institutions
      )
""")
updated_brazil = cursor.rowcount
print(f"  ✅ Atualizados {updated_brazil:,} registros via brazil_research_institutions")
conn.commit()

# 4. Atualizar country usando dim_university (se tiver country_id)
print("4. Tentando atualizar via dim_university...")
cursor.execute("""
    UPDATE sofia.persons p
    SET country = du.country_id
    FROM sofia.dim_university du
    WHERE p.primary_affiliation = du.university_code
      AND du.country_id IS NOT NULL
      AND (p.country IS NULL OR p.country = '')
""")
updated_dim = cursor.rowcount
print(f"  ✅ Atualizados {updated_dim:,} registros via dim_university")
conn.commit()

# 5. Verificar situação DEPOIS
print()
print("5. Situação DEPOIS da correção:")
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN country IS NOT NULL AND country != '' THEN 1 END) as with_country
    FROM sofia.persons
""")
row = cursor.fetchone()
print(f"  Total persons: {row[0]:,}")
print(f"  Com country: {row[1]:,} ({row[1]*100.0/row[0]:.1f}%)")
print()

# 6. Mostrar distribuição por país
print("6. Distribuição por país (Top 10):")
cursor.execute("""
    SELECT country, COUNT(*) as count
    FROM sofia.persons
    WHERE country IS NOT NULL AND country != ''
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]:>8} persons")
print()

# 7. Verificar quantos papers agora têm país
print("7. Papers com país (via persons):")
cursor.execute("""
    SELECT 
        COUNT(DISTINCT pp.id) as total_papers,
        COUNT(DISTINCT CASE WHEN p.country IS NOT NULL AND p.country != '' THEN pp.id END) as papers_with_country
    FROM sofia.person_papers pp
    JOIN sofia.persons p ON pp.person_id = p.id
""")
row = cursor.fetchone()
print(f"  Total papers: {row[0]:,}")
print(f"  Papers com país: {row[1]:,} ({row[1]*100.0/row[0]:.1f}%)")
print()

print("=" * 80)
print("✅ CAMPO COUNTRY PREENCHIDO COM SUCESSO!")
print("=" * 80)
print()
print(f"Total de registros atualizados: {updated_global + updated_brazil + updated_dim:,}")
print()

cursor.close()
conn.close()
