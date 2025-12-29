-- ============================================================
-- OPTIMIZED ANALYTICS QUERIES
-- Using normalized geographic IDs for better performance
-- ============================================================

-- 1. Jobs by Country (OPTIMIZED)
SELECT 
    c.common_name as country,
    c.iso_alpha2 as code,
    COUNT(*) as total_jobs
FROM sofia.jobs j
JOIN sofia.countries c ON j.country_id = c.id
GROUP BY c.id, c.common_name, c.iso_alpha2
ORDER BY total_jobs DESC
LIMIT 20;

-- 2. Jobs by Country + State (OPTIMIZED)
SELECT 
    c.common_name as country,
    s.name as state,
    COUNT(*) as total_jobs
FROM sofia.jobs j
JOIN sofia.countries c ON j.country_id = c.id
LEFT JOIN sofia.states s ON j.state_id = s.id
WHERE j.state_id IS NOT NULL
GROUP BY c.id, c.common_name, s.id, s.name
ORDER BY total_jobs DESC
LIMIT 20;

-- 3. Multi-table Geographic Analysis (OPTIMIZED)
SELECT 
    c.common_name as country,
    COUNT(DISTINCT j.id) as jobs,
    COUNT(DISTINCT d.id) as drug_data,
    COUNT(DISTINCT w.id) as women_data
FROM sofia.countries c
LEFT JOIN sofia.jobs j ON j.country_id = c.id
LEFT JOIN sofia.world_drugs_data d ON d.country_id = c.id
LEFT JOIN sofia.women_brazil_data w ON w.country_id = c.id
GROUP BY c.id, c.common_name
HAVING COUNT(DISTINCT j.id) > 0 
    OR COUNT(DISTINCT d.id) > 0
ORDER BY jobs DESC;

-- 4. Remote vs On-site Jobs by Country (OPTIMIZED)
SELECT 
    c.common_name as country,
    COUNT(*) FILTER (WHERE j.city_id IS NULL) as remote_jobs,
    COUNT(*) FILTER (WHERE j.city_id IS NOT NULL) as onsite_jobs
FROM sofia.jobs j
JOIN sofia.countries c ON j.country_id = c.id
GROUP BY c.id, c.common_name
ORDER BY (remote_jobs + onsite_jobs) DESC
LIMIT 20;

-- 5. Top Cities for Jobs (OPTIMIZED)
SELECT 
    c.common_name as country,
    s.name as state,
    ci.name as city,
    COUNT(*) as jobs
FROM sofia.jobs j
JOIN sofia.countries c ON j.country_id = c.id
JOIN sofia.cities ci ON j.city_id = ci.id
LEFT JOIN sofia.states s ON j.state_id = s.id
GROUP BY c.id, c.common_name, s.id, s.name, ci.id, ci.name
ORDER BY jobs DESC
LIMIT 50;

-- 6. Data Completeness Report (OPTIMIZED)
SELECT 
    'jobs' as table_name,
    COUNT(*) as total_records,
    COUNT(country_id) as with_country_id,
    ROUND(100.0 * COUNT(country_id) / COUNT(*), 2) as pct_coverage
FROM sofia.jobs
UNION ALL
SELECT 
    'world_drugs_data',
    COUNT(*),
    COUNT(country_id),
    ROUND(100.0 * COUNT(country_id) / COUNT(*), 2)
FROM sofia.world_drugs_data
UNION ALL
SELECT 
    'women_brazil_data',
    COUNT(*),
    COUNT(country_id),
    ROUND(100.0 * COUNT(country_id) / COUNT(*), 2)
FROM sofia.women_brazil_data
ORDER BY table_name;

-- 7. Countries with Most Data Coverage (OPTIMIZED)
SELECT 
    c.common_name,
    c.iso_alpha2,
    COUNT(DISTINCT j.id) as jobs,
    COUNT(DISTINCT d.id) as drugs,
    COUNT(DISTINCT w.id) as women,
    COUNT(DISTINCT s.id) as sports,
    COUNT(DISTINCT t.id) as tourism
FROM sofia.countries c
LEFT JOIN sofia.jobs j ON j.country_id = c.id
LEFT JOIN sofia.world_drugs_data d ON d.country_id = c.id  
LEFT JOIN sofia.women_brazil_data w ON w.country_id = c.id
LEFT JOIN sofia.world_sports_data s ON s.country_id = c.id
LEFT JOIN sofia.world_tourism_data t ON t.country_id = c.id
GROUP BY c.id, c.common_name, c.iso_alpha2
ORDER BY (jobs + drugs + women + sports + tourism) DESC
LIMIT 30;
