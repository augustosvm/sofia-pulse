#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Collect ArXiv papers (rate limited)
npx tsx scripts/collect.ts arxiv

# Sync data to legacy tables for cross-signals
PGPASSWORD="${POSTGRES_PASSWORD:-SofiaPulse2025Secure@DB}" psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-sofia}" -d "${POSTGRES_DB:-sofia_db}" << 'SQL'
-- Sync ArXiv from research_papers to arxiv_ai_papers
INSERT INTO sofia.arxiv_ai_papers (
    arxiv_id, title, authors, categories, abstract, published_date,
    updated_date, pdf_url, primary_category, keywords, is_breakthrough, collected_at
)
SELECT
    source_id, title, authors, categories, abstract, publication_date,
    publication_date, pdf_url, primary_category, keywords,
    is_breakthrough, collected_at
FROM sofia.research_papers
WHERE source = 'arxiv' AND collected_at >= NOW() - INTERVAL '2 hours'
ON CONFLICT (arxiv_id) DO UPDATE SET
    title = EXCLUDED.title, abstract = EXCLUDED.abstract,
    published_date = EXCLUDED.published_date, collected_at = EXCLUDED.collected_at;
SQL

echo "✅ Limited APIs collected and synced"
