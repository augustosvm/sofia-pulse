#!/bin/bash
# Run NIH Grants VARCHAR limits fix migration

set -e

echo "🔧 Applying NIH Grants VARCHAR Limits Fix..."

# Load env vars
source .env 2>/dev/null || true

# PostgreSQL connection
export PGPASSWORD="${DB_PASSWORD}"
PSQL="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}"

# Apply migration
$PSQL -f migrations/002-fix-nih-grants-varchar-limits.sql

echo "✅ Migration applied successfully!"
echo "   You can now re-run collect-nih-grants.ts"
