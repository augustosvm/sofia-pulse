-- ============================================================================
-- Sofia Pulse - Análise Regional de Papers (COPIAR E COLAR NO PSQL)
-- ============================================================================
--
-- INSTRUÇÕES:
-- 1. Conecte ao banco: ssh ubuntu@91.98.158.19
-- 2. Execute: psql -U sofia -d sofia_db
-- 3. Copie e cole este arquivo inteiro no terminal psql
--
-- ============================================================================

\echo '🚀 Sofia Pulse - Análise Regional de Papers'
\echo '================================================================================'
\echo ''

-- ============================================================================
-- 1. CRIAR FUNÇÃO DE MAPEAMENTO
-- ============================================================================

\echo '🔧 Criando função de mapeamento de países para regiões...'

CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  IF country_code = 'BR' THEN RETURN 'Brasil';
  ELSIF country_code IN ('US', 'CA', 'MX') THEN RETURN 'América do Norte';
  ELSIF country_code IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU', 'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME', 'RS', 'XK', 'MD', 'UA', 'BY', 'RU') THEN RETURN 'Europa';
  ELSIF country_code IN ('CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID', 'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN', 'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR', 'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM', 'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG') THEN RETURN 'Ásia';
  ELSIF country_code IN ('AU', 'NZ', 'FJ', 'PG', 'NC', 'PF', 'WS', 'TO', 'VU', 'SB', 'KI', 'FM', 'MH', 'PW', 'NR', 'TV') THEN RETURN 'Oceania';
  ELSIF country_code IN ('ZA', 'EG', 'NG', 'KE', 'ET', 'GH', 'TZ', 'UG', 'DZ', 'MA', 'AO', 'SD', 'MZ', 'MG', 'CM', 'CI', 'NE', 'BF', 'ML', 'MW', 'ZM', 'SN', 'SO', 'TD', 'GN', 'RW', 'BJ', 'TN', 'BI', 'SS', 'TG', 'SL', 'LY', 'LR', 'MR', 'CF', 'ER', 'GM', 'BW', 'GA', 'GW', 'GQ', 'MU', 'SZ', 'DJ', 'RE', 'KM', 'CV', 'ST', 'SC') THEN RETURN 'África';
  ELSIF country_code IN ('AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO', 'PY', 'UY', 'GY', 'SR', 'GF', 'CR', 'PA', 'CU', 'DO', 'GT', 'HN', 'SV', 'NI', 'BZ', 'JM', 'TT', 'BS', 'BB', 'LC', 'GD', 'VC', 'AG', 'DM', 'KN', 'HT', 'PR', 'VI', 'AW', 'CW', 'BQ', 'SX', 'MF', 'BL') THEN RETURN 'América Latina';
  ELSE RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

\echo '✅ Função criada!'
\echo ''

-- ============================================================================
-- 2. ESTATÍSTICAS GERAIS POR REGIÃO
-- ============================================================================

\echo '================================================================================'
\echo '📊 ESTATÍSTICAS GERAIS POR REGIÃO'
\echo '================================================================================'
\echo ''

WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.cited_by_count,
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
    WHEN 'América Latina' THEN '🌎 América Latina'
    WHEN 'África' THEN '🌍 África'
  END AS "Região",
  COUNT(DISTINCT p.id) AS "Total Papers",
  SUM(p.cited_by_count) AS "Total Citações",
  AVG(p.cited_by_count)::INT AS "Média Citações",
  ROUND(
    COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
    SUM(COUNT(DISTINCT p.id)) OVER (),
    2
  ) || '%' AS "% Global"
FROM papers_with_regions p
CROSS JOIN UNNEST(p.regions) AS region
WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'América Latina', 'África')
GROUP BY region
ORDER BY COUNT(DISTINCT p.id) DESC;

\echo ''

-- ============================================================================
-- 3. ASSUNTO #1 POR REGIÃO
-- ============================================================================

\echo '================================================================================'
\echo '📊 ASSUNTO #1 MAIS CITADO POR REGIÃO'
\echo '================================================================================'
\echo ''

WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.cited_by_count,
    p.primary_concept,
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020
),
region_stats AS (
  SELECT 
    region,
    primary_concept,
    COUNT(DISTINCT p.id) AS paper_count,
    SUM(p.cited_by_count) AS total_citations,
    ROUND(
      COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
      SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region),
      2
    ) AS percentage
  FROM papers_with_regions p
  CROSS JOIN UNNEST(p.regions) AS region
  WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
  GROUP BY region, primary_concept
),
top_per_region AS (
  SELECT 
    region,
    primary_concept,
    paper_count,
    percentage,
    total_citations,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY paper_count DESC) AS rank
  FROM region_stats
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
  END AS "Região",
  primary_concept AS "Assunto #1",
  paper_count AS "Papers",
  percentage || '%' AS "% da Região",
  total_citations AS "Citações"
FROM top_per_region
WHERE rank = 1
ORDER BY 
  CASE region
    WHEN 'Brasil' THEN 1
    WHEN 'América do Norte' THEN 2
    WHEN 'Europa' THEN 3
    WHEN 'Ásia' THEN 4
    WHEN 'Oceania' THEN 5
  END;

\echo ''

-- ============================================================================
-- 4. TOP 5 ASSUNTOS POR REGIÃO
-- ============================================================================

\echo '================================================================================'
\echo '📊 TOP 5 ASSUNTOS MAIS CITADOS POR REGIÃO'
\echo '================================================================================'
\echo ''

WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.cited_by_count,
    p.concepts,
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020
),
region_concept_stats AS (
  SELECT 
    region,
    concept,
    COUNT(DISTINCT p.id) AS paper_count,
    SUM(p.cited_by_count) AS total_citations,
    ROUND(
      COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
      SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region),
      2
    ) AS percentage
  FROM papers_with_regions p
  CROSS JOIN UNNEST(p.regions) AS region
  CROSS JOIN UNNEST(p.concepts) AS concept
  WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
  GROUP BY region, concept
),
ranked_concepts AS (
  SELECT 
    region,
    concept,
    paper_count,
    percentage,
    total_citations,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY paper_count DESC) AS rank
  FROM region_concept_stats
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
  END AS "Região",
  rank AS "#",
  concept AS "Assunto",
  paper_count AS "Papers",
  percentage || '%' AS "%",
  total_citations AS "Citações"
FROM ranked_concepts
WHERE rank <= 5
ORDER BY 
  CASE region
    WHEN 'Brasil' THEN 1
    WHEN 'América do Norte' THEN 2
    WHEN 'Europa' THEN 3
    WHEN 'Ásia' THEN 4
    WHEN 'Oceania' THEN 5
  END,
  rank;

\echo ''
\echo '================================================================================'
\echo '✅ ANÁLISE CONCLUÍDA'
\echo '================================================================================'
\echo ''
\echo '💡 COMPARAÇÃO COM DADOS FORNECIDOS:'
\echo ''
\echo '   🇧🇷 Brasil: AI Ethics - 1,234 papers - 28%'
\echo '   🇺🇸 América do Norte: LLMs - 5,678 papers - 42%'
\echo '   🇪🇺 Europa: Quantum AI - 3,456 papers - 35%'
\echo '   🌏 Ásia: Computer Vision - 6,789 papers - 44%'
\echo '   🇦🇺 Oceania: Climate AI - 892 papers - 31%'
\echo ''
\echo '   Compare os resultados acima com estes dados fornecidos!'
\echo ''
