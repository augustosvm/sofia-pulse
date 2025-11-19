CREATE TABLE IF NOT EXISTS sofia.reddit_tech (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(50) UNIQUE NOT NULL,
    subreddit VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    author VARCHAR(100),
    score INT DEFAULT 0,
    num_comments INT DEFAULT 0,
    url TEXT,
    created_utc TIMESTAMP,
    technologies TEXT[],
    sentiment VARCHAR(20),
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reddit_subreddit ON sofia.reddit_tech(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_score ON sofia.reddit_tech(score DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_created ON sofia.reddit_tech(created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_tech ON sofia.reddit_tech USING GIN(technologies);
