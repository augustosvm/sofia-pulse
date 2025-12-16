-- ============================================================================
-- Sofia Pulse - Análise de Papers por Região Geográfica
-- ============================================================================
-- 
-- Este arquivo contém queries SQL para analisar os assuntos mais citados
-- em papers científicos por região geográfica.
--
-- Fonte de dados: openalex_papers (250M+ papers)
-- Campo de região: author_countries (array de códigos ISO de países)
-- Campo de assuntos: concepts (array de conceitos/tópicos)
-- ============================================================================

-- ============================================================================
-- 1. MAPEAMENTO DE PAÍSES PARA REGIÕES
-- ============================================================================

-- Função auxiliar para mapear código de país para região
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  -- Brasil
  IF country_code = 'BR' THEN
    RETURN 'Brasil';
  
  -- América do Norte
  ELSIF country_code IN ('US', 'CA', 'MX') THEN
    RETURN 'América do Norte';
  
  -- Europa
  ELSIF country_code IN (
    'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 
    'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO',
    'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU',
    'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME',
    'RS', 'XK', 'MD', 'UA', 'BY', 'RU'
  ) THEN
    RETURN 'Europa';
  
  -- Ásia
  ELSIF country_code IN (
    'CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID',
    'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN',
    'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR',
    'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM',
    'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG'
  ) THEN
    RETURN 'Ásia';
  
  -- Oceania
  ELSIF country_code IN ('AU', 'NZ', 'FJ', 'PG', 'NC', 'PF', 'WS', 'TO', 'VU', 'SB', 'KI', 'FM', 'MH', 'PW', 'NR', 'TV') THEN
    RETURN 'Oceania';
  
  -- África
  ELSIF country_code IN (
    'ZA', 'EG', 'NG', 'KE', 'ET', 'GH', 'TZ', 'UG', 'DZ', 'MA',
    'AO', 'SD', 'MZ', 'MG', 'CM', 'CI', 'NE', 'BF', 'ML', 'MW',
    'ZM', 'SN', 'SO', 'TD', 'GN', 'RW', 'BJ', 'TN', 'BI', 'SS',
    'TG', 'SL', 'LY', 'LR', 'MR', 'CF', 'ER', 'GM', 'BW', 'GA',
    'GW', 'GQ', 'MU', 'SZ', 'DJ', 'RE', 'KM', 'CV', 'ST', 'SC'
  ) THEN
    RETURN 'África';
  
  -- América Latina (exceto Brasil)
  ELSIF country_code IN (
    'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO', 'PY', 'UY', 'GY',
    'SR', 'GF', 'CR', 'PA', 'CU', 'DO', 'GT', 'HN', 'SV', 'NI',
    'BZ', 'JM', 'TT', 'BS', 'BB', 'LC', 'GD', 'VC', 'AG', 'DM',
    'KN', 'HT', 'PR', 'VI', 'AW', 'CW', 'BQ', 'SX', 'MF', 'BL'
  ) THEN
    RETURN 'América Latina';
  
  ELSE
    RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 2. ASSUNTOS MAIS CITADOS POR REGIÃO
-- ============================================================================

-- Query principal: Top 10 assuntos mais citados por região
WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.openalex_id,
    p.title,
    p.publication_year,
    p.cited_by_count,
    p.concepts,
    p.primary_concept,
    p.author_countries,
    -- Mapeia cada país para sua região
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020  -- Últimos anos
),
region_concept_stats AS (
  SELECT 
    region,
    concept,
    COUNT(DISTINCT p.id) AS paper_count,
    SUM(p.cited_by_count) AS total_citations,
    AVG(p.cited_by_count)::INT AS avg_citations,
    ROUND(
      COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
      SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region),
      2
    ) AS percentage_of_region
  FROM papers_with_regions p
  CROSS JOIN UNNEST(p.regions) AS region
  CROSS JOIN UNNEST(p.concepts) AS concept
  WHERE region != 'Outros'  -- Exclui países não mapeados
  GROUP BY region, concept
)
SELECT 
  region AS "Região",
  concept AS "Assunto/Conceito",
  paper_count AS "Quantidade de Papers",
  percentage_of_region AS "% do Total da Região",
  total_citations AS "Total de Citações",
  avg_citations AS "Média de Citações",
  -- Ranking dentro da região
  ROW_NUMBER() OVER (PARTITION BY region ORDER BY paper_count DESC) AS ranking_por_papers,
  ROW_NUMBER() OVER (PARTITION BY region ORDER BY total_citations DESC) AS ranking_por_citacoes
FROM region_concept_stats
WHERE paper_count >= 5  -- Filtro: pelo menos 5 papers
ORDER BY 
  region,
  paper_count DESC;

-- ============================================================================
-- 3. TOP 5 ASSUNTOS POR REGIÃO (RESUMO)
-- ============================================================================

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
  region AS "🌍 Região",
  concept AS "Assunto Mais Citado",
  paper_count AS "Papers",
  percentage || '%' AS "% do Total",
  total_citations AS "Citações Totais"
FROM ranked_concepts
WHERE rank <= 5  -- Top 5 por região
ORDER BY 
  CASE region
    WHEN 'Brasil' THEN 1
    WHEN 'América do Norte' THEN 2
    WHEN 'Europa' THEN 3
    WHEN 'Ásia' THEN 4
    WHEN 'Oceania' THEN 5
  END,
  rank;

-- ============================================================================
-- 4. ASSUNTO #1 POR REGIÃO (MAIS SIMPLES)
-- ============================================================================

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
  percentage || '% do total' AS "Percentual"
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

-- ============================================================================
-- 5. ESTATÍSTICAS GERAIS POR REGIÃO
-- ============================================================================

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
  region AS "Região",
  COUNT(DISTINCT p.id) AS "Total de Papers",
  SUM(p.cited_by_count) AS "Total de Citações",
  AVG(p.cited_by_count)::INT AS "Média de Citações por Paper",
  ROUND(
    COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
    SUM(COUNT(DISTINCT p.id)) OVER (),
    2
  ) AS "% do Total Global"
FROM papers_with_regions p
CROSS JOIN UNNEST(p.regions) AS region
WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'América Latina', 'África')
GROUP BY region
ORDER BY "Total de Papers" DESC;

-- ============================================================================
-- 6. COMPARAÇÃO: DADOS REAIS vs DADOS FORNECIDOS
-- ============================================================================

-- Esta query compara os dados reais do banco com os dados que você forneceu
-- Para executar, primeiro rode a query #4 e compare os resultados

/*
DADOS FORNECIDOS PELO USUÁRIO:
🇧🇷 Brasil: AI Ethics - 1,234 papers - 28% do total
🇺🇸 América do Norte: LLMs - 5,678 papers - 42% do total
🇪🇺 Europa: Quantum AI - 3,456 papers - 35% do total
🌏 Ásia: Computer Vision - 6,789 papers - 44% do total
🇦🇺 Oceania: Climate AI - 892 papers - 31% do total
🌍 Mundo: Multimodal AI - 18,234 papers - 52% do total global

PARA VALIDAR:
1. Execute a query #4 para ver o assunto #1 real por região
2. Execute a query #5 para ver as estatísticas gerais
3. Compare os percentuais e números absolutos
4. Verifique se os assuntos batem com a realidade
*/

-- ============================================================================
-- 7. BUSCA POR ASSUNTOS ESPECÍFICOS
-- ============================================================================

-- Query para verificar se os assuntos mencionados existem nos dados
WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.concepts,
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
  region AS "Região",
  concept AS "Assunto",
  COUNT(DISTINCT p.id) AS "Quantidade de Papers"
FROM papers_with_regions p
CROSS JOIN UNNEST(p.regions) AS region
CROSS JOIN UNNEST(p.concepts) AS concept
WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
  AND (
    concept ILIKE '%AI Ethics%' OR
    concept ILIKE '%LLM%' OR
    concept ILIKE '%Large Language%' OR
    concept ILIKE '%Quantum%' OR
    concept ILIKE '%Computer Vision%' OR
    concept ILIKE '%Climate%' OR
    concept ILIKE '%Multimodal%'
  )
GROUP BY region, concept
ORDER BY region, "Quantidade de Papers" DESC;

-- ============================================================================
-- NOTAS DE USO:
-- ============================================================================
--
-- 1. A função map_country_to_region() precisa ser criada primeiro
-- 2. As queries assumem que openalex_papers tem dados de 2020+
-- 3. Ajuste o filtro de ano conforme necessário
-- 4. Os percentuais são calculados dentro de cada região
-- 5. Papers podem aparecer em múltiplas regiões (coautoria internacional)
--
-- ============================================================================
