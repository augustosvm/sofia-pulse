-- Health Check Queries for LLM Enrichment Pipeline
-- Check enrichment status and recent runs

-- 1. Count items needing enrichment
SELECT
    COUNT(*) FILTER (WHERE extracted_topics IS NULL OR array_length(extracted_topics, 1) IS NULL) as missing_topics,
    COUNT(*) FILTER (WHERE extracted_entities IS NULL) as missing_entities,
    COUNT(*) FILTER (WHERE extracted_topics IS NOT NULL AND array_length(extracted_topics, 1) > 0) as has_topics,
    COUNT(*) FILTER (WHERE extracted_entities IS NOT NULL) as has_entities,
    COUNT(*) as total
FROM sofia.news_items
WHERE source = 'hackernews';

-- 2. Sample enriched items
SELECT
    id,
    title,
    extracted_topics,
    extracted_entities->'companies' as companies,
    extracted_entities->'technologies' as technologies,
    published_at
FROM sofia.news_items
WHERE source = 'hackernews'
  AND extracted_topics IS NOT NULL
ORDER BY published_at DESC NULLS LAST
LIMIT 10;

-- 3. Recent enrichment runs
SELECT
    run_id,
    started_at AT TIME ZONE 'America/Sao_Paulo' as started_brt,
    finished_at AT TIME ZONE 'America/Sao_Paulo' as finished_brt,
    EXTRACT(EPOCH FROM (finished_at - started_at)) / 60 as duration_minutes,
    model,
    processed,
    enriched,
    cache_hits,
    llm_calls,
    errors,
    status
FROM sofia.llm_enrichment_runs
ORDER BY started_at DESC
LIMIT 10;

-- 4. Cache statistics
SELECT
    source,
    model,
    prompt_version,
    COUNT(*) as cache_entries,
    MIN(created_at) as oldest_entry,
    MAX(created_at) as newest_entry
FROM sofia.llm_enrichment_cache
GROUP BY source, model, prompt_version
ORDER BY source, model, prompt_version;

-- 5. Top topics extracted
SELECT
    topic,
    COUNT(*) as count
FROM sofia.news_items,
     unnest(extracted_topics) as topic
WHERE source = 'hackernews'
GROUP BY topic
ORDER BY count DESC
LIMIT 20;

-- 6. Top companies mentioned
SELECT
    company,
    COUNT(*) as count
FROM sofia.news_items,
     jsonb_array_elements_text(extracted_entities->'companies') as company
WHERE source = 'hackernews'
  AND extracted_entities IS NOT NULL
GROUP BY company
ORDER BY count DESC
LIMIT 20;

-- 7. Daily API usage (for budget monitoring)
SELECT
    DATE(started_at) as date,
    COUNT(*) as runs,
    SUM(llm_calls) as total_api_calls,
    SUM(processed) as total_processed,
    SUM(enriched) as total_enriched
FROM sofia.llm_enrichment_runs
WHERE started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;
