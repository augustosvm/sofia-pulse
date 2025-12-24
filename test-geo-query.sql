-- Teste de query SQL para normalização geográfica
-- Verificar se alias co/ci funcionam

-- Teste 1: Query simples
SELECT
    COALESCE(ci.name, fr.city, co.name, 'Unknown') as city,
    COALESCE(co.name, fr.country, 'Unknown') as country,
    COUNT(*) as deals_count
FROM sofia.funding_rounds fr
LEFT JOIN sofia.countries co ON fr.country_id = co.id
LEFT JOIN sofia.cities ci ON fr.city_id = ci.id
WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '365 days'
    AND (fr.country_id IS NOT NULL OR fr.country IS NOT NULL)
GROUP BY ci.name, fr.city, co.name, fr.country
LIMIT 10;

-- Teste 2: Verificar se tabelas existem
SELECT COUNT(*) FROM sofia.countries;
SELECT COUNT(*) FROM sofia.cities;
SELECT COUNT(*) FROM sofia.funding_rounds WHERE country_id IS NOT NULL;
