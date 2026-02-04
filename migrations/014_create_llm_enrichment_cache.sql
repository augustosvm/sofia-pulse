-- Migration: Create LLM enrichment cache table
-- Date: 2026-02-04
-- Purpose: Cache Gemini API responses to avoid duplicate calls and save costs

BEGIN;

-- Cache table for LLM enrichment results
CREATE TABLE IF NOT EXISTS sofia.llm_enrichment_cache (
    cache_key TEXT PRIMARY KEY,  -- sha256(title + '|' + url)
    source TEXT NOT NULL,         -- e.g. 'hackernews', 'reddit', etc.
    model TEXT NOT NULL,          -- e.g. 'gemini-2.0-flash', 'gemini-1.5-flash'
    prompt_version TEXT NOT NULL, -- e.g. 'v1', 'v2' (to invalidate cache on prompt changes)
    input_data JSONB NOT NULL,    -- { "title": "...", "url": "..." }
    result JSONB NOT NULL,        -- { "topics": [...], "entities": {...} }
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tokens_used INTEGER,          -- optional: track token usage
    cost_usd DECIMAL(10, 6)       -- optional: track costs
);

-- Index for finding cache by source/model/version
CREATE INDEX IF NOT EXISTS idx_llm_cache_source_model
    ON sofia.llm_enrichment_cache(source, model, prompt_version);

-- Index for expiration/cleanup (cache entries older than 90 days)
CREATE INDEX IF NOT EXISTS idx_llm_cache_created
    ON sofia.llm_enrichment_cache(created_at);

-- Enrichment runs tracking table
CREATE TABLE IF NOT EXISTS sofia.llm_enrichment_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    source TEXT NOT NULL,         -- 'hackernews', etc.
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    limit_requested INTEGER,      -- --limit parameter
    processed INTEGER DEFAULT 0,
    enriched INTEGER DEFAULT 0,   -- items successfully enriched
    cache_hits INTEGER DEFAULT 0,
    llm_calls INTEGER DEFAULT 0,  -- actual API calls made
    errors INTEGER DEFAULT 0,
    error_details JSONB,          -- array of error messages
    budget_limit_hit BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'running' -- 'running', 'completed', 'failed', 'budget_exceeded'
);

-- Index for finding recent runs
CREATE INDEX IF NOT EXISTS idx_llm_runs_started
    ON sofia.llm_enrichment_runs(started_at DESC);

COMMIT;

-- Verification queries:
-- SELECT COUNT(*) FROM sofia.llm_enrichment_cache;
-- SELECT * FROM sofia.llm_enrichment_runs ORDER BY started_at DESC LIMIT 5;
