-- Technical News Items (HackerNews + other sources)
-- Unified table for technical news aggregation

CREATE TABLE IF NOT EXISTS sofia.news_items (
  id SERIAL PRIMARY KEY,

  -- Source identity
  source TEXT NOT NULL,                 -- 'hackernews', 'reddit', 'lobsters', 'devto', etc
  external_id TEXT NOT NULL,            -- Source's native ID (e.g., HN item_id)

  -- Content
  title TEXT NOT NULL,
  url TEXT,                             -- Article URL (null for Ask HN, Show HN without link)
  text_content TEXT,                    -- Body text for self-posts
  item_type TEXT,                       -- 'story', 'ask', 'show', 'poll', 'job'

  -- Metrics
  score INT DEFAULT 0,                  -- Points/upvotes
  comment_count INT DEFAULT 0,          -- Number of comments
  rank INT,                             -- Position in trending/frontpage (null if not ranked)

  -- Metadata
  author TEXT,                          -- Username who posted
  published_at TIMESTAMPTZ,             -- When item was created/published
  fetched_at TIMESTAMPTZ DEFAULT NOW(), -- When we collected this snapshot

  -- Entity extraction (for cross-signal matching)
  extracted_entities JSONB,             -- {companies: [], technologies: [], frameworks: [], people: []}
  extracted_topics TEXT[],              -- ['rust', 'async', 'performance']

  -- Engagement tracking
  first_seen_rank INT,                  -- First rank position we saw (to detect velocity)
  peak_rank INT,                        -- Best rank position achieved
  time_on_frontpage_hours NUMERIC(5,2), -- How long it stayed ranked

  -- Constraints
  UNIQUE(source, external_id, fetched_at::DATE)  -- Allow daily snapshots
);

-- Indexes for fast queries
CREATE INDEX idx_news_source ON sofia.news_items(source);
CREATE INDEX idx_news_published ON sofia.news_items(published_at DESC);
CREATE INDEX idx_news_fetched ON sofia.news_items(fetched_at DESC);
CREATE INDEX idx_news_score ON sofia.news_items(score DESC);
CREATE INDEX idx_news_rank ON sofia.news_items(rank) WHERE rank IS NOT NULL;
CREATE INDEX idx_news_topics ON sofia.news_items USING gin(extracted_topics);
CREATE INDEX idx_news_entities ON sofia.news_items USING gin(extracted_entities);

-- Composite index for "trending in last 7 days"
CREATE INDEX idx_news_trending_7d ON sofia.news_items(source, published_at DESC, score DESC)
  WHERE published_at >= NOW() - INTERVAL '7 days';

-- Materialized view for daily high-impact stories (candidates for events)
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.news_items_high_impact AS
SELECT
  id,
  source,
  external_id,
  title,
  url,
  published_at,
  score,
  comment_count,
  rank,
  extracted_entities,
  extracted_topics,
  -- Impact score: weighted combination of score, comments, rank
  CASE
    WHEN rank IS NOT NULL THEN
      (score::NUMERIC / NULLIF(rank, 0)) * LOG(1 + comment_count)
    ELSE
      score * LOG(1 + comment_count) * 0.5  -- Non-ranked items get penalty
  END AS impact_score
FROM sofia.news_items
WHERE
  published_at >= NOW() - INTERVAL '7 days'
  AND score >= 50  -- Minimum threshold
ORDER BY
  CASE
    WHEN rank IS NOT NULL THEN (score::NUMERIC / NULLIF(rank, 0)) * LOG(1 + comment_count)
    ELSE score * LOG(1 + comment_count) * 0.5
  END DESC
LIMIT 100;

CREATE INDEX idx_news_high_impact_score ON sofia.news_items_high_impact(impact_score DESC);
CREATE INDEX idx_news_high_impact_topics ON sofia.news_items_high_impact USING gin(extracted_topics);

COMMENT ON TABLE sofia.news_items IS 'Unified technical news aggregation (HN, Reddit, etc) with entity extraction for cross-signals';
COMMENT ON MATERIALIZED VIEW sofia.news_items_high_impact IS 'Top 100 high-impact stories from last 7 days (refresh daily before cross-signals builder)';
