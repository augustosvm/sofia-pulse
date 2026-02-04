# PHASE 5B - LLM ENRICHMENT FOR CROSS-SIGNALS

**Date:** 2026-02-04 23:00 UTC
**Status:** ✅ READY FOR DEPLOYMENT
**Purpose:** Fill `extracted_topics` and `extracted_entities` in `news_items` to enable cross-signals insights

---

## 🎯 PROBLEM STATEMENT

**Issue**: Cross-signals generates JSON but **0 insights/observations**

**Root Cause**: `sofia.news_items.extracted_topics` and `extracted_entities` are **NULL** for HackerNews items

**Impact**: Cross-correlations fail:
- HackerNews topics ↔ GitHub trending topics
- HackerNews entities ↔ Funding rounds companies
- HackerNews topics ↔ ArXiv keywords

---

## ✅ SOLUTION

**LLM Enrichment Pipeline** using Google Gemini to extract:

1. **Topics** (TEXT[]):
   - 3-12 items per article
   - Lowercase, single words or short phrases
   - Examples: `["rust", "webassembly", "machine learning", "kubernetes"]`

2. **Entities** (JSONB):
   ```json
   {
     "companies": ["OpenAI", "Google", "Amazon"],
     "technologies": ["Rust", "Kubernetes", "PostgreSQL"],
     "products": ["ChatGPT", "Chrome", "VS Code"],
     "people": ["Linus Torvalds", "Guido van Rossum"],
     "countries": ["USA", "China", "India"],
     "projects": ["Linux Kernel", "LLVM", "TensorFlow"]
   }
   ```

---

## 📋 COMPONENTS

### **1. Database Tables**

**Migration**: `migrations/014_create_llm_enrichment_cache.sql`

**Tables Created**:
- `sofia.llm_enrichment_cache` - Caches API responses (avoids duplicate calls)
- `sofia.llm_enrichment_runs` - Tracks each enrichment run (observability)

**Schema**:
```sql
llm_enrichment_cache:
  - cache_key (PK) - SHA256 of title + url
  - source, model, prompt_version
  - input_data, result (JSONB)
  - created_at, tokens_used, cost_usd

llm_enrichment_runs:
  - run_id (PK UUID)
  - started_at, finished_at
  - source, model, prompt_version
  - processed, enriched, cache_hits, llm_calls, errors
  - status ('running', 'completed', 'failed', 'budget_exceeded')
```

---

### **2. Enrichment Script**

**File**: `scripts/enrich-hackernews-items-gemini.py`

**Features**:
- ✅ Connects to Postgres (POSTGRES_* env vars)
- ✅ Selects items WHERE `extracted_topics IS NULL OR extracted_entities IS NULL`
- ✅ Checks cache first (SHA256 key = title + url)
- ✅ Calls Gemini API with structured JSON prompt
- ✅ Validates and normalizes response
- ✅ Updates `news_items` table
- ✅ Saves to cache
- ✅ Rate limiting (1 req/sec)
- ✅ Retry on 429 (rate limit)
- ✅ Daily budget guardrail
- ✅ Comprehensive logging

**Guardrails**:
- **Daily Budget**: Stops at `GEMINI_DAILY_CALL_LIMIT` (default 500)
- **Timeout**: 30s per request
- **Retry**: Automatic on 429 (rate limit)
- **Validation**: JSON parsing with error handling
- **Dry Run**: `--dry-run` flag for testing

---

### **3. SQL Helpers**

**File**: `outputs/health/enrichment_check.sql`

**Queries**:
1. Count items needing enrichment
2. Sample enriched items
3. Recent enrichment runs
4. Cache statistics
5. Top topics extracted
6. Top companies mentioned
7. Daily API usage (budget monitoring)

---

## 🚀 SETUP

### **1. Apply Migration**

```bash
# On server
cd ~/sofia-pulse
psql "postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db" -f migrations/014_create_llm_enrichment_cache.sql
```

**Verification**:
```sql
SELECT COUNT(*) FROM sofia.llm_enrichment_cache;
SELECT COUNT(*) FROM sofia.llm_enrichment_runs;
```

---

### **2. Set Environment Variables**

```bash
# Add to .env file
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp  # or gemini-1.5-flash
GEMINI_DAILY_CALL_LIMIT=500
```

**Get API Key**:
- Go to: https://aistudio.google.com/app/apikey
- Create API key
- Add to `.env`

---

## 📊 USAGE

### **Basic Usage**

```bash
# Enrich 200 items (default)
python3 scripts/enrich-hackernews-items-gemini.py

# Enrich 500 items
python3 scripts/enrich-hackernews-items-gemini.py --limit 500

# Dry run (test without updating DB)
python3 scripts/enrich-hackernews-items-gemini.py --limit 50 --dry-run
```

---

### **Check Status Before Running**

```bash
# How many items need enrichment?
psql "postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db" -c "
SELECT
    COUNT(*) FILTER (WHERE extracted_topics IS NULL) as missing_topics,
    COUNT(*) FILTER (WHERE extracted_entities IS NULL) as missing_entities,
    COUNT(*) as total
FROM sofia.news_items
WHERE source = 'hackernews';
"
```

---

### **Monitor Progress**

```bash
# Check recent runs
psql "postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db" -f outputs/health/enrichment_check.sql
```

---

### **Example Output**

```
================================================================================
GEMINI LLM ENRICHMENT - HACKERNEWS ITEMS
================================================================================
Model: gemini-2.0-flash-exp
Prompt Version: v1
Limit: 200
Dry Run: False
Daily Budget: 500 calls
================================================================================

✅ Database connected
📊 Found 187 items to enrich

[1/187] Processing item 12345...
      🔄 Calling Gemini API (id=12345): New Rust async runtime beats Tokio in benchmarks...
      ✅ Enriched: 5 topics, 8 entities
[2/187] Processing item 12346...
      ✅ Cache hit (id=12346)
[3/187] Processing item 12347...
      🔄 Calling Gemini API (id=12347): OpenAI announces GPT-5 with reasoning capabilities...
      ✅ Enriched: 7 topics, 12 entities
...

================================================================================
ENRICHMENT COMPLETE
================================================================================
Processed:    187
Enriched:     187
Cache Hits:   45
LLM Calls:    142
Errors:       0
Dry Run:      False
================================================================================
```

---

## 🔄 WORKFLOW

### **Complete Enrichment → Cross-Signals Pipeline**

```bash
# 1. Enrich HackerNews items
cd ~/sofia-pulse
python3 scripts/enrich-hackernews-items-gemini.py --limit 500

# 2. Run cross-signals builder
python3 scripts/build-cross-signals.py --window-days 7

# 3. Verify results
cat outputs/cross_signals.json | jq '.summary'
```

**Expected Results**:
```json
{
  "summary": {
    "sources_used": 4,
    "total_observations": 15,
    "total_insights": 3,
    "coverage": {
      "hackernews": 156,
      "github_trending": 89,
      "funding_rounds": 23,
      "arxiv_ai_papers": 12
    }
  }
}
```

---

## 📈 VALIDATION QUERIES

### **1. Check Enrichment Coverage**

```sql
SELECT
    COUNT(*) as total_items,
    COUNT(*) FILTER (WHERE extracted_topics IS NOT NULL AND array_length(extracted_topics, 1) > 0) as has_topics,
    COUNT(*) FILTER (WHERE extracted_entities IS NOT NULL) as has_entities,
    ROUND(100.0 * COUNT(*) FILTER (WHERE extracted_topics IS NOT NULL) / COUNT(*), 2) as pct_topics,
    ROUND(100.0 * COUNT(*) FILTER (WHERE extracted_entities IS NOT NULL) / COUNT(*), 2) as pct_entities
FROM sofia.news_items
WHERE source = 'hackernews';
```

**Expected**:
```
total_items | has_topics | has_entities | pct_topics | pct_entities
------------+------------+--------------+------------+-------------
       1245 |       1245 |         1245 |     100.00 |       100.00
```

---

### **2. Sample Enriched Items**

```sql
SELECT
    title,
    extracted_topics,
    extracted_entities->'companies' as companies,
    extracted_entities->'technologies' as technologies
FROM sofia.news_items
WHERE source = 'hackernews'
  AND extracted_topics IS NOT NULL
ORDER BY published_at DESC NULLS LAST
LIMIT 5;
```

**Expected Output**:
```
title                                    | extracted_topics                           | companies              | technologies
-----------------------------------------+--------------------------------------------+------------------------+---------------------------
New Rust async runtime beats Tokio       | ["rust","async","performance","tokio"]     | ["Tokio"]              | ["Rust","async/await"]
OpenAI announces GPT-5                   | ["ai","llm","openai","gpt"]                | ["OpenAI"]             | ["GPT","LLM"]
Kubernetes 1.30 released                 | ["kubernetes","devops","containers"]       | ["Google","CNCF"]      | ["Kubernetes","Docker"]
```

---

### **3. Top Topics**

```sql
SELECT
    topic,
    COUNT(*) as count
FROM sofia.news_items,
     unnest(extracted_topics) as topic
WHERE source = 'hackernews'
GROUP BY topic
ORDER BY count DESC
LIMIT 20;
```

**Expected Top Topics**:
```
topic            | count
-----------------+-------
ai               |   324
rust             |   156
machine learning |   142
kubernetes       |   127
webassembly      |   98
python           |   87
```

---

### **4. Top Companies**

```sql
SELECT
    company,
    COUNT(*) as mentions
FROM sofia.news_items,
     jsonb_array_elements_text(extracted_entities->'companies') as company
WHERE source = 'hackernews'
  AND extracted_entities IS NOT NULL
GROUP BY company
ORDER BY mentions DESC
LIMIT 20;
```

**Expected Top Companies**:
```
company   | mentions
----------+---------
OpenAI    |      89
Google    |      67
Amazon    |      45
Microsoft |      42
Meta      |      38
```

---

## 💰 COST ESTIMATION

**Gemini API Pricing** (as of 2024):
- **gemini-2.0-flash-exp**: FREE (experimental)
- **gemini-1.5-flash**: $0.00001875 per 1K chars input, $0.000075 per 1K chars output

**Estimated Cost per Item**:
- Input: ~300 chars (title + URL + prompt) = $0.0000056
- Output: ~500 chars (JSON) = $0.0000375
- **Total: ~$0.000043 per item**

**For 1000 items**: ~$0.043 (4 cents)

**For 10,000 items**: ~$0.43 (43 cents)

**Daily Budget at 500 calls**: ~$0.022 (2 cents)

**Note**: Using `gemini-2.0-flash-exp` (experimental) is **FREE** as of Feb 2026.

---

## 🔍 TROUBLESHOOTING

### **API Key Not Set**

```
❌ Error: GEMINI_API_KEY environment variable not set
```

**Fix**:
```bash
# Add to .env
GEMINI_API_KEY=your_api_key_here
```

---

### **Rate Limit Exceeded**

```
⚠️  Rate limit hit, retrying in 5s...
```

**Cause**: Gemini API free tier has rate limits

**Fix**: Script automatically retries after 5s

---

### **Daily Budget Exceeded**

```
⚠️  Daily budget exceeded: 502/500 calls made today
```

**Fix**:
```bash
# Increase limit in .env
GEMINI_DAILY_CALL_LIMIT=1000

# Or wait until tomorrow (resets at midnight UTC)
```

---

### **JSON Parse Error**

```
❌ JSON Parse Error: Expecting value: line 1 column 1
```

**Cause**: Gemini returned invalid JSON (rare)

**Fix**: Script skips item and continues. Check `error_details` in `llm_enrichment_runs` table.

---

### **Database Connection Failed**

```
❌ Database connection failed: fe_sendauth: no password supplied
```

**Fix**: Check `POSTGRES_*` env vars in `.env`

---

## 📊 MONITORING

### **Check Daily API Usage**

```sql
SELECT
    DATE(started_at) as date,
    SUM(llm_calls) as total_api_calls,
    SUM(processed) as items_processed,
    SUM(enriched) as items_enriched,
    SUM(cache_hits) as cache_hits,
    ROUND(100.0 * SUM(cache_hits) / NULLIF(SUM(processed), 0), 2) as cache_hit_rate_pct
FROM sofia.llm_enrichment_runs
WHERE started_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;
```

---

### **Check Cache Efficiency**

```sql
SELECT
    COUNT(*) as cache_entries,
    COUNT(DISTINCT source) as sources,
    COUNT(DISTINCT model) as models,
    MIN(created_at) as oldest_entry,
    MAX(created_at) as newest_entry,
    ROUND(AVG(tokens_used), 0) as avg_tokens,
    SUM(cost_usd) as total_cost_usd
FROM sofia.llm_enrichment_cache;
```

---

## 🚀 NEXT STEPS

### **1. Initial Enrichment** (one-time)

```bash
# Enrich all existing items (may take a while)
python3 scripts/enrich-hackernews-items-gemini.py --limit 1000

# Check progress
psql "..." -f outputs/health/enrichment_check.sql
```

---

### **2. Add to Daily Pipeline** (optional)

**Option A**: Manual run before cross-signals
```bash
# In crontab, before cross-signals builder
25 21 * * 1-5 cd ~/sofia-pulse && python3 scripts/enrich-hackernews-items-gemini.py --limit 100 >> logs/enrichment.log 2>&1
30 21 * * 1-5 cd ~/sofia-pulse && bash run-cross-signals-builder.sh >> logs/cross-signals.log 2>&1
```

**Option B**: Integrate into collector
- Add enrichment step to `collect-hackernews.ts` or wrapper
- Run enrichment immediately after collection

---

### **3. Optimize Cache**

```sql
-- Delete old cache entries (>90 days)
DELETE FROM sofia.llm_enrichment_cache
WHERE created_at < NOW() - INTERVAL '90 days';

-- Vacuum to reclaim space
VACUUM ANALYZE sofia.llm_enrichment_cache;
```

---

## 📝 FILES CREATED

**Migrations**:
- `migrations/014_create_llm_enrichment_cache.sql` (cache + runs tables)

**Scripts**:
- `scripts/enrich-hackernews-items-gemini.py` (enrichment pipeline)

**SQL Helpers**:
- `outputs/health/enrichment_check.sql` (monitoring queries)

**Documentation**:
- `PHASE5B-LLM-ENRICHMENT.md` (this file)

---

## ✅ SUCCESS CRITERIA

After enrichment, cross-signals should produce:

1. **sources_used >= 3** (HackerNews, GitHub, Funding, ArXiv)
2. **total_observations > 0** (at least some correlations found)
3. **coverage.hackernews > 0** (HN items being cross-referenced)

**Validation**:
```bash
python3 scripts/build-cross-signals.py --window-days 7
cat outputs/cross_signals.json | jq '.summary'
```

**Expected**:
```json
{
  "sources_used": 4,
  "total_observations": 15,
  "coverage": {
    "hackernews": 156,
    "github_trending": 89,
    "funding_rounds": 23,
    "arxiv_ai_papers": 12
  }
}
```

---

## 🎯 CONCLUSION

This enrichment pipeline:
- ✅ Fills missing `extracted_topics` and `extracted_entities`
- ✅ Enables cross-signals correlations
- ✅ Uses caching to minimize API costs
- ✅ Has daily budget guardrails
- ✅ Provides comprehensive monitoring
- ✅ Is idempotent and safe

**Next**: Run enrichment, then rebuild cross-signals to see insights! 🚀

---

**Last Updated**: 2026-02-04 23:00 UTC
**Status**: Ready for deployment
