#!/bin/bash
set -e

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔧 CRIANDO TABELAS MANUALMENTE"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Load .env
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_HOST="${POSTGRES_HOST:-${DB_HOST:-localhost}}"
DB_PORT="${POSTGRES_PORT:-${DB_PORT:-5432}}"
DB_USER="${POSTGRES_USER:-${DB_USER:-sofia}}"
DB_NAME="${POSTGRES_DB:-${DB_NAME:-sofia_db}}"
DB_PASS="${POSTGRES_PASSWORD:-${DB_PASSWORD}}"

echo "📊 Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Create space_industry table
echo "🚀 Creating space_industry table..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOSQL'
CREATE TABLE IF NOT EXISTS sofia.space_industry (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    mission_name VARCHAR(200),
    company VARCHAR(100),
    launch_date TIMESTAMP,
    launch_site VARCHAR(200),
    rocket_type VARCHAR(100),
    payload_type VARCHAR(100),
    payload_count INTEGER,
    orbit_type VARCHAR(50),
    status VARCHAR(50),
    customers TEXT[],
    contract_value_usd BIGINT,
    country VARCHAR(100),
    description TEXT,
    source VARCHAR(100),
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_space_type ON sofia.space_industry(event_type);
CREATE INDEX IF NOT EXISTS idx_space_company ON sofia.space_industry(company);
CREATE INDEX IF NOT EXISTS idx_space_date ON sofia.space_industry(launch_date);
CREATE INDEX IF NOT EXISTS idx_space_status ON sofia.space_industry(status);
EOSQL
echo "   ✅ space_industry criada"
echo ""

# Create ai_regulation table
echo "⚖️  Creating ai_regulation table..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOSQL'
CREATE TABLE IF NOT EXISTS sofia.ai_regulation (
    id SERIAL PRIMARY KEY,
    regulation_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    jurisdiction VARCHAR(100),
    regulatory_body VARCHAR(200),
    status VARCHAR(50),
    effective_date DATE,
    announced_date DATE,
    scope TEXT[],
    impact_level VARCHAR(20),
    penalties_max BIGINT,
    description TEXT,
    key_requirements TEXT[],
    affected_sectors TEXT[],
    source VARCHAR(100),
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, jurisdiction)
);

CREATE INDEX IF NOT EXISTS idx_reg_type ON sofia.ai_regulation(regulation_type);
CREATE INDEX IF NOT EXISTS idx_reg_jurisdiction ON sofia.ai_regulation(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_reg_status ON sofia.ai_regulation(status);
CREATE INDEX IF NOT EXISTS idx_reg_date ON sofia.ai_regulation(announced_date);
EOSQL
echo "   ✅ ai_regulation criada"
echo ""

echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ TABELAS CRIADAS COM SUCESSO!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
