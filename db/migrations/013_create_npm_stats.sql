CREATE TABLE IF NOT EXISTS sofia.npm_stats (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR(200) NOT NULL,
    downloads_day INT DEFAULT 0,
    downloads_week INT DEFAULT 0,
    downloads_month INT DEFAULT 0,
    version VARCHAR(50),
    description TEXT,
    keywords TEXT[],
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Create unique index on package_name and date (using expression)
CREATE UNIQUE INDEX IF NOT EXISTS idx_npm_package_date ON sofia.npm_stats(package_name, DATE(collected_at));
CREATE INDEX IF NOT EXISTS idx_npm_package ON sofia.npm_stats(package_name);
CREATE INDEX IF NOT EXISTS idx_npm_downloads ON sofia.npm_stats(downloads_month DESC);
CREATE INDEX IF NOT EXISTS idx_npm_date ON sofia.npm_stats(collected_at DESC);
