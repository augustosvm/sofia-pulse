#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
npx tsx scripts/collect.ts github
npx tsx scripts/collect.ts hackernews

# Sync data to legacy tables for cross-signals
PGPASSWORD="${POSTGRES_PASSWORD:-SofiaPulse2025Secure@DB}" psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-sofia}" -d "${POSTGRES_DB:-sofia_db}" << 'SQL'
-- Sync GitHub from tech_trends to github_trending
INSERT INTO sofia.github_trending (
    repo_id, full_name, owner, name, description, homepage, language,
    stars, forks, watchers, open_issues, topics, license,
    is_fork, is_archived, created_at, updated_at, pushed_at, collected_at
)
SELECT
    (metadata->>'repo_id')::bigint, name, metadata->>'owner',
    SPLIT_PART(name, '/', 2), metadata->>'description', metadata->>'homepage',
    category, stars, forks, (metadata->>'watchers')::int,
    (metadata->>'open_issues')::int,
    ARRAY(SELECT jsonb_array_elements_text(metadata->'topics'))::text[],
    metadata->>'license', (metadata->>'is_fork')::boolean,
    (metadata->>'is_archived')::boolean,
    (metadata->>'created_at')::timestamp,
    (metadata->>'updated_at')::timestamp,
    (metadata->>'pushed_at')::timestamp,
    collected_at
FROM sofia.tech_trends
WHERE source = 'github' AND collected_at >= NOW() - INTERVAL '2 hours'
ON CONFLICT (repo_id) DO UPDATE SET
    full_name = EXCLUDED.full_name, stars = EXCLUDED.stars,
    forks = EXCLUDED.forks, collected_at = EXCLUDED.collected_at;

-- Sync HackerNews from hackernews_stories to news_items
INSERT INTO sofia.news_items (
    source, external_id, title, url, score, comment_count,
    author, published_at, fetched_at
)
SELECT
    'hackernews', story_id::text, title, url, points, num_comments,
    author, created_at, collected_at
FROM sofia.hackernews_stories
WHERE collected_at >= NOW() - INTERVAL '2 hours'
ON CONFLICT (source, external_id, (fetched_at::date)) DO UPDATE SET
    title = EXCLUDED.title, score = EXCLUDED.score;
SQL

echo "✅ Fast APIs collected and synced"
