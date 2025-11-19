#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🗄️  RUNNING DATABASE MIGRATIONS"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database configuration with fallbacks
DB_HOST="${POSTGRES_HOST:-${DB_HOST:-localhost}}"
DB_PORT="${POSTGRES_PORT:-${DB_PORT:-5432}}"
DB_USER="${POSTGRES_USER:-${DB_USER:-sofia}}"
DB_NAME="${POSTGRES_DB:-${DB_NAME:-sofia_db}}"
DB_PASS="${POSTGRES_PASSWORD:-${DB_PASSWORD}}"

echo "📊 Database Configuration:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo ""

# Migrations to run
MIGRATIONS=(
    "db/migrations/011_create_gdelt_events.sql"
    "db/migrations/012_create_reddit_tech.sql"
    "db/migrations/013_create_npm_stats.sql"
    "db/migrations/014_create_pypi_stats.sql"
)

echo "🔄 Running migrations..."
echo ""

for migration in "${MIGRATIONS[@]}"; do
    if [ -f "$migration" ]; then
        echo "   Running $(basename $migration)..."
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration" 2>&1 | grep -E "(CREATE|ERROR|already exists)" || echo "      ✅ OK"
    else
        echo "   ⚠️  Migration not found: $migration"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ MIGRATIONS COMPLETE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Verify tables were created:"
echo ""
echo "  PGPASSWORD=\"\$DB_PASSWORD\" psql -h \"$DB_HOST\" -p \"$DB_PORT\" -U \"$DB_USER\" -d \"$DB_NAME\" -c \"\\\dt sofia.*\""
echo ""
