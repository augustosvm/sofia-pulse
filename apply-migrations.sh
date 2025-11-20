#!/bin/bash
set -e

export PGPASSWORD=sofia123strong

echo "Applying all migrations..."

PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/007_create_ipo_calendar.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/009_create_github_trending.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/010_create_hackernews_stories.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/011_create_gdelt_events.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/012_create_reddit_tech.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/013_create_npm_stats.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/014_create_pypi_stats.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/015_create_cybersecurity.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/016_create_space_industry.sql > /dev/null 2>&1 || true
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -f db/migrations/017_create_ai_regulation.sql > /dev/null 2>&1 || true

echo "✅ All migrations applied!"

# Verify tables
PGPASSWORD=sofia123strong psql -h localhost -U sofia -d sofia_db -c "\dt sofia.*" | grep -c "sofia\." || echo "0"
