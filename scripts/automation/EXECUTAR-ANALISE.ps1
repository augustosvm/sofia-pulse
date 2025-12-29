# ============================================================================
# Sofia Pulse - Análise Regional de Papers
# Execute este arquivo: .\EXECUTAR-ANALISE.ps1
# ============================================================================

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Sofia Pulse - Análise Regional de Papers" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executando análise no servidor como ROOT..." -ForegroundColor Yellow
Write-Host ""

# Comando SQL completo
$sqlCommand = @"
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS `$`$ BEGIN
  IF country_code = 'BR' THEN RETURN 'Brasil';
  ELSIF country_code IN ('US', 'CA', 'MX') THEN RETURN 'América do Norte';
  ELSIF country_code IN ('CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID', 'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN', 'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR', 'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM', 'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG') THEN RETURN 'Ásia';
  ELSIF country_code IN ('AU', 'NZ') THEN RETURN 'Oceania';
  ELSIF country_code IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU', 'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME', 'RS', 'XK', 'MD', 'UA', 'BY', 'RU') THEN RETURN 'Europa';
  ELSE RETURN 'Outros';
  END IF;
END; `$`$ LANGUAGE plpgsql IMMUTABLE;

WITH papers_with_regions AS (
  SELECT p.id, p.cited_by_count, p.primary_concept,
    ARRAY(SELECT DISTINCT map_country_to_region(country) FROM UNNEST(p.author_countries) AS country) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL AND array_length(p.author_countries, 1) > 0 AND p.publication_year >= 2020
),
region_stats AS (
  SELECT region, primary_concept, COUNT(DISTINCT p.id) AS paper_count,
    ROUND(COUNT(DISTINCT p.id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region), 2) AS percentage
  FROM papers_with_regions p CROSS JOIN UNNEST(p.regions) AS region
  WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
  GROUP BY region, primary_concept
),
top_per_region AS (
  SELECT region, primary_concept, paper_count, percentage,
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
  END AS \"Região\",
  primary_concept AS \"Assunto #1\",
  paper_count AS \"Papers\",
  percentage || '%' AS \"% Região\"
FROM top_per_region
WHERE rank = 1
ORDER BY CASE region WHEN 'Brasil' THEN 1 WHEN 'América do Norte' THEN 2 WHEN 'Europa' THEN 3 WHEN 'Ásia' THEN 4 WHEN 'Oceania' THEN 5 END;
"@

# Executar via SSH
ssh root@91.98.158.19 "psql -U sofia -d sofia_db -c `"$sqlCommand`""

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "✅ ANÁLISE CONCLUÍDA" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "💡 COMPARAÇÃO COM DADOS FORNECIDOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   🇧🇷 Brasil: AI Ethics - 1,234 papers - 28%"
Write-Host "   🇺🇸 América do Norte: LLMs - 5,678 papers - 42%"
Write-Host "   🇪🇺 Europa: Quantum AI - 3,456 papers - 35%"
Write-Host "   🌏 Ásia: Computer Vision - 6,789 papers - 44%"
Write-Host "   🇦🇺 Oceania: Climate AI - 892 papers - 31%"
Write-Host ""
