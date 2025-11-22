#!/bin/bash
################################################################################
# APPLY CITY MIGRATIONS - Add city and countries columns
################################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "📊 APPLYING CITY MIGRATIONS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Load env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-sofia_db}"
DB_USER="${POSTGRES_USER:-sofia}"

echo "Target database:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Apply migration 008 - Add city column
echo "📊 Migration 008: Adding city column to funding_rounds..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrations/008-add-city-column.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration 008 applied successfully"
else
    echo "❌ Migration 008 failed"
    exit 1
fi

echo ""

# Apply migration 009 - Add countries column
echo "📊 Migration 009: Adding countries column to openalex_papers..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrations/009-add-countries-column-openalex.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration 009 applied successfully"
else
    echo "❌ Migration 009 failed"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL MIGRATIONS APPLIED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "New columns added:"
echo "  • sofia.funding_rounds.city (VARCHAR 200)"
echo "  • sofia.openalex_papers.countries (TEXT[])"
echo ""
echo "Next steps:"
echo "  1. Update collectors to populate these columns"
echo "  2. Run analytics: bash run-mega-analytics.sh"
echo ""

