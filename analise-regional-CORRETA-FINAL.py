#!/usr/bin/env python3
"""
ANÁLISE REGIONAL CORRETA usando person_papers JOIN persons
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

print("📊 ANÁLISE REGIONAL CORRETA - person_papers JOIN persons")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# 1. Ver quantos persons têm country preenchido
print("1. Verificando cobertura de país em persons:")
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN country IS NOT NULL AND country != '' THEN 1 END) as with_country,
        COUNT(CASE WHEN primary_affiliation IS NOT NULL THEN 1 END) as with_affiliation
    FROM sofia.persons
""")
row = cursor.fetchone()
print(f"  Total persons: {row[0]:,}")
print(f"  Com country: {row[1]:,} ({row[1]*100.0/row[0]:.1f}%)")
print(f"  Com affiliation: {row[2]:,} ({row[2]*100.0/row[0]:.1f}%)")
print()

# 2. Ver distribuição de countries
print("2. Top 10 países em persons:")
cursor.execute("""
    SELECT country, COUNT(*) as count
    FROM sofia.persons
    WHERE country IS NOT NULL AND country != ''
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]:>6} persons")
print()

# 3. Criar função de mapeamento
cursor.execute("""
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  IF country_code = 'BR' OR country_code = 'Brazil' THEN RETURN 'Brasil';
  ELSIF country_code IN ('US', 'CA', 'MX', 'United States', 'Canada', 'Mexico') THEN RETURN 'América do Norte';
  ELSIF country_code IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU', 'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME', 'RS', 'XK', 'MD', 'UA', 'BY', 'RU', 'United Kingdom', 'Germany', 'France', 'Italy', 'Spain') THEN RETURN 'Europa';
  ELSIF country_code IN ('CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID', 'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN', 'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR', 'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM', 'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG', 'China', 'Japan', 'India', 'South Korea') THEN RETURN 'Ásia';
  ELSIF country_code IN ('AU', 'NZ', 'Australia', 'New Zealand') THEN RETURN 'Oceania';
  ELSIF country_code IN ('ZA', 'EG', 'NG', 'KE', 'ET', 'GH', 'TZ', 'UG', 'DZ', 'MA', 'South Africa', 'Egypt') THEN RETURN 'África';
  ELSE RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
""")
conn.commit()

# 4. Análise regional com JOIN correto
print("3. TOP 5 ASSUNTOS POR REGIÃO (usando person_papers JOIN persons):")
print("=" * 80)
print()

cursor.execute("""
WITH papers_with_region AS (
    SELECT 
        pp.id,
        pp.keywords,
        map_country_to_region(p.country) as region
    FROM sofia.person_papers pp
    JOIN sofia.persons p ON pp.person_id = p.id
    WHERE p.country IS NOT NULL 
      AND p.country != ''
      AND pp.keywords IS NOT NULL
      AND pp.published_date >= '2020-01-01'
),
keywords_by_region AS (
    SELECT 
        region,
        UNNEST(keywords) as keyword,
        COUNT(DISTINCT id) as papers,
        ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (PARTITION BY region), 2) as pct_region
    FROM papers_with_region
    WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'África')
    GROUP BY region, keyword
),
ranked_keywords AS (
    SELECT 
        region,
        keyword,
        papers,
        pct_region,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY papers DESC) as rank
    FROM keywords_by_region
)
SELECT 
    CASE region
        WHEN 'Brasil' THEN '🇧🇷 Brasil'
        WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
        WHEN 'Europa' THEN '🇪🇺 Europa'
        WHEN 'Ásia' THEN '🌏 Ásia'
        WHEN 'Oceania' THEN '🇦🇺 Oceania'
        WHEN 'África' THEN '🌍 África'
    END AS regiao,
    rank,
    keyword,
    papers,
    pct_region
FROM ranked_keywords
WHERE rank <= 5
ORDER BY 
    CASE region
        WHEN 'Brasil' THEN 1
        WHEN 'América do Norte' THEN 2
        WHEN 'Europa' THEN 3
        WHEN 'Ásia' THEN 4
        WHEN 'Oceania' THEN 5
        WHEN 'África' THEN 6
    END,
    rank
""")

results = cursor.fetchall()
current_region = None

for row in results:
    if row[0] != current_region:
        if current_region is not None:
            print()
        current_region = row[0]
        print(f"\n{row[0]}")
        print("-" * 80)
    
    print(f"  {row[1]}. {row[2]:<45} {row[3]:>6} papers ({row[4]:>5}%)")

print()
print("=" * 80)
print("✅ ANÁLISE CONCLUÍDA COM MAPEAMENTO CORRETO")
print("=" * 80)
print()

cursor.close()
conn.close()
