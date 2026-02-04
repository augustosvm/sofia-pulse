-- Health Check for Phase 3 Recovered Collectors
-- Reports: record count (last 24h), latest insert, total records
-- Exit 1 if any collector has 0 records in last 24h

-- 1. World Sports Data
SELECT
    'world-sports' as collector,
    COUNT(*) FILTER (WHERE collected_at >= NOW() - INTERVAL '24 hours') as records_24h,
    COUNT(*) as total_records,
    MAX(collected_at) as latest_insert,
    MAX(collected_at) >= NOW() - INTERVAL '24 hours' as is_healthy
FROM sofia.world_sports_data;

-- 2. HDX Humanitarian Data
SELECT
    'hdx-humanitarian' as collector,
    COUNT(*) FILTER (WHERE collected_at >= NOW() - INTERVAL '24 hours') as records_24h,
    COUNT(*) as total_records,
    MAX(collected_at) as latest_insert,
    MAX(collected_at) >= NOW() - INTERVAL '24 hours' as is_healthy
FROM sofia.hdx_humanitarian_data;

-- 3. Sports Regional
SELECT
    'sports-regional' as collector,
    COUNT(*) FILTER (WHERE collected_at >= NOW() - INTERVAL '24 hours') as records_24h,
    COUNT(*) as total_records,
    MAX(collected_at) as latest_insert,
    MAX(collected_at) >= NOW() - INTERVAL '24 hours' as is_healthy
FROM sofia.sports_regional;

-- 4. Women Brazil Data
SELECT
    'women-brazil' as collector,
    COUNT(*) FILTER (WHERE collected_at >= NOW() - INTERVAL '24 hours') as records_24h,
    COUNT(*) as total_records,
    MAX(collected_at) as latest_insert,
    MAX(collected_at) >= NOW() - INTERVAL '24 hours' as is_healthy
FROM sofia.women_brazil_data;

-- Summary
WITH health_status AS (
    SELECT 1 as has_data FROM sofia.world_sports_data WHERE collected_at >= NOW() - INTERVAL '24 hours' LIMIT 1
    UNION ALL
    SELECT 1 FROM sofia.hdx_humanitarian_data WHERE collected_at >= NOW() - INTERVAL '24 hours' LIMIT 1
    UNION ALL
    SELECT 1 FROM sofia.sports_regional WHERE collected_at >= NOW() - INTERVAL '24 hours' LIMIT 1
    UNION ALL
    SELECT 1 FROM sofia.women_brazil_data WHERE collected_at >= NOW() - INTERVAL '24 hours' LIMIT 1
)
SELECT
    'SUMMARY' as collector,
    (SELECT COUNT(*) FROM health_status) as healthy_collectors,
    4 as total_collectors,
    CASE
        WHEN (SELECT COUNT(*) FROM health_status) = 4 THEN 'HEALTHY'
        ELSE 'DEGRADED'
    END as overall_status;
