CREATE TABLE IF NOT EXISTS sofia.pypi_stats (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR(200) NOT NULL,
    downloads_month INT DEFAULT 0,
    version VARCHAR(50),
    description TEXT,
    keywords TEXT[],
    collected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(package_name, DATE(collected_at))
);

CREATE INDEX IF NOT EXISTS idx_pypi_package ON sofia.pypi_stats(package_name);
CREATE INDEX IF NOT EXISTS idx_pypi_downloads ON sofia.pypi_stats(downloads_month DESC);
CREATE INDEX IF NOT EXISTS idx_pypi_date ON sofia.pypi_stats(collected_at DESC);
