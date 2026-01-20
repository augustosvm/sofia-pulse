-- Fast ACLED Normalization: regional -> security_events
-- Uses direct INSERT ... SELECT (instant!)

-- Clear old ACLED data
DELETE FROM sofia.security_events WHERE source = 'ACLED';

-- Insert ALL regional data at once
INSERT INTO sofia.security_events (
    source,
    source_id,
    event_date,
    country_name,
    country_code,
    latitude,
    longitude,
    event_type,
    fatalities,
    raw_payload
)
SELECT
    'ACLED',
    md5(CONCAT('acled_v3_', dataset_slug, '_', country, '_', COALESCE(admin1,''), '_', year, '_', month, '_', week, '_', centroid_latitude, '_', centroid_longitude, '_', event_type)),
    MAKE_DATE(year, COALESCE(month, 1), 1),  -- Simplified: year-month-01
    country,
    NULL,  -- country_code (TODO: join with dim_country)
    centroid_latitude,
    centroid_longitude,
    event_type,
    COALESCE(fatalities, 0),
    jsonb_build_object(
        'dataset_slug', dataset_slug,
        'admin1', admin1,
        'admin2', admin2,
        'disorder_type', disorder_type,
        'events', events,
        'year', year,
        'month', month,
        'week', week
    )
FROM acled_aggregated.regional
WHERE centroid_latitude IS NOT NULL
  AND centroid_longitude IS NOT NULL
ON CONFLICT (source, source_id) DO NOTHING;

-- Show results
SELECT
    COUNT(*) as total,
    COUNT(DISTINCT country_name) as countries,
    MIN(event_date) as earliest,
    MAX(event_date) as latest
FROM sofia.security_events
WHERE source = 'ACLED';
