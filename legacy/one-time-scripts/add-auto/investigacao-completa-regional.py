#!/usr/bin/env python3
"""
INVESTIGAÇÃO COMPLETA: Mapeamento Regional de Papers
1. Buscar tags específicas (LLMs, AI Ethics, etc)
2. Verificar relacionamento entre tabelas
3. Analisar por ano
4. Identificar especialização regional real
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

print("🔍 INVESTIGAÇÃO COMPLETA: Mapeamento Regional de Papers")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# ============================================================================
# 1. BUSCAR TAGS ESPECÍFICAS
# ============================================================================

print("=" * 80)
print("1️⃣ BUSCANDO TAGS ESPECÍFICAS DE IA")
print("=" * 80)
print()

specific_tags = {
    'LLMs': ['LLM', 'Large language model', 'GPT', 'BERT', 'Transformer', 'Language model'],
    'AI Ethics': ['AI ethics', 'Responsible AI', 'Fairness', 'Bias', 'Explainability', 'XAI'],
    'Multimodal': ['Multimodal', 'Vision-language', 'CLIP', 'Cross-modal']
}

for category, keywords in specific_tags.items():
    conditions = " OR ".join([f"keywords::text ILIKE '%{kw}%'" for kw in keywords])
    
    cursor.execute(f"""
        SELECT COUNT(DISTINCT id) as count
        FROM sofia.person_papers
        WHERE keywords IS NOT NULL
          AND ({conditions})
    """)
    
    count = cursor.fetchone()[0]
    print(f"{category:<20} {count:>6} papers")
    
    if count > 0:
        # Mostrar exemplos de keywords encontradas
        cursor.execute(f"""
            SELECT DISTINCT UNNEST(keywords) as keyword
            FROM sofia.person_papers
            WHERE keywords IS NOT NULL
              AND ({conditions})
            LIMIT 10
        """)
        print(f"  Exemplos: {', '.join([row[0] for row in cursor.fetchall()])}")
    print()

# ============================================================================
# 2. VERIFICAR RELACIONAMENTO ENTRE TABELAS
# ============================================================================

print("=" * 80)
print("2️⃣ VERIFICANDO RELACIONAMENTO ENTRE TABELAS")
print("=" * 80)
print()

# Ver como person_papers se relaciona com global_universities_progress
cursor.execute("""
    SELECT 
        pp.paper_source,
        COUNT(DISTINCT pp.id) as total_papers,
        COUNT(DISTINCT CASE WHEN gu.country_code IS NOT NULL THEN pp.id END) as papers_with_country
    FROM sofia.person_papers pp
    LEFT JOIN sofia.global_universities_progress gu 
      ON pp.paper_source = 'global_university'
    GROUP BY pp.paper_source
""")

print("Relacionamento person_papers <-> global_universities_progress:")
for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]:>8} papers total, {row[2]:>8} com país")

print()

# Ver distribuição de países em global_universities_progress
cursor.execute("""
    SELECT 
        country_code,
        COUNT(*) as institutions,
        SUM(papers_collected) as total_papers
    FROM sofia.global_universities_progress
    WHERE country_code IS NOT NULL
    GROUP BY country_code
    ORDER BY total_papers DESC
    LIMIT 10
""")

print("Top 10 países em global_universities_progress:")
for row in cursor.fetchall():
    print(f"  {row[0]:<5} {row[1]:>3} instituições, {row[2]:>8} papers")

print()

# ============================================================================
# 3. ANALISAR POR ANO
# ============================================================================

print("=" * 80)
print("3️⃣ DISTRIBUIÇÃO DE PAPERS POR ANO")
print("=" * 80)
print()

cursor.execute("""
    SELECT 
        EXTRACT(YEAR FROM published_date) as year,
        COUNT(*) as papers
    FROM sofia.person_papers
    WHERE published_date IS NOT NULL
    GROUP BY year
    ORDER BY year DESC
    LIMIT 10
""")

print("Papers por ano (últimos 10 anos):")
for row in cursor.fetchall():
    if row[0]:
        print(f"  {int(row[0])}: {row[1]:>8} papers")

print()

# ============================================================================
# 4. VERIFICAR OPENALEX_PAPERS (tem author_countries)
# ============================================================================

print("=" * 80)
print("4️⃣ ANALISANDO OPENALEX_PAPERS (com author_countries)")
print("=" * 80)
print()

cursor.execute("""
    SELECT 
        UNNEST(author_countries) as country,
        COUNT(*) as papers
    FROM openalex_papers
    WHERE author_countries IS NOT NULL
    GROUP BY country
    ORDER BY papers DESC
    LIMIT 10
""")

print("Top 10 países em openalex_papers:")
for row in cursor.fetchall():
    print(f"  {row[0]:<5} {row[1]:>6} papers")

print()

# ============================================================================
# 5. BUSCAR ESPECIALIZAÇÃO REGIONAL
# ============================================================================

print("=" * 80)
print("5️⃣ BUSCANDO ESPECIALIZAÇÃO REGIONAL (openalex_papers)")
print("=" * 80)
print()

# Criar função de mapeamento
cursor.execute("""
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  IF country_code = 'BR' THEN RETURN 'Brasil';
  ELSIF country_code IN ('US', 'CA', 'MX') THEN RETURN 'América do Norte';
  ELSIF country_code IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU', 'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME', 'RS', 'XK', 'MD', 'UA', 'BY', 'RU') THEN RETURN 'Europa';
  ELSIF country_code IN ('CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID', 'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN', 'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR', 'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM', 'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG') THEN RETURN 'Ásia';
  ELSIF country_code IN ('AU', 'NZ') THEN RETURN 'Oceania';
  ELSE RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
""")
conn.commit()

# Analisar top concepts por região em openalex_papers
cursor.execute("""
WITH papers_by_region AS (
    SELECT 
        p.id,
        p.concepts,
        map_country_to_region(UNNEST(p.author_countries)) as region
    FROM openalex_papers p
    WHERE p.author_countries IS NOT NULL
      AND p.publication_year >= 2020
),
concept_by_region AS (
    SELECT 
        region,
        UNNEST(concepts) as concept,
        COUNT(DISTINCT id) as papers
    FROM papers_by_region
    WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
    GROUP BY region, concept
),
ranked_concepts AS (
    SELECT 
        region,
        concept,
        papers,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY papers DESC) as rank
    FROM concept_by_region
)
SELECT 
    CASE region
        WHEN 'Brasil' THEN '🇧🇷 Brasil'
        WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
        WHEN 'Europa' THEN '🇪🇺 Europa'
        WHEN 'Ásia' THEN '🌏 Ásia'
        WHEN 'Oceania' THEN '🇦🇺 Oceania'
    END AS regiao,
    rank,
    concept,
    papers
FROM ranked_concepts
WHERE rank <= 3
ORDER BY 
    CASE region
        WHEN 'Brasil' THEN 1
        WHEN 'América do Norte' THEN 2
        WHEN 'Europa' THEN 3
        WHEN 'Ásia' THEN 4
        WHEN 'Oceania' THEN 5
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
    
    print(f"  {row[1]}. {row[2]:<40} {row[3]:>6} papers")

print()
print("=" * 80)
print("✅ INVESTIGAÇÃO CONCLUÍDA")
print("=" * 80)
print()

cursor.close()
conn.close()
