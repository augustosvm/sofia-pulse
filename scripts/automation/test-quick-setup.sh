#!/bin/bash
# Quick test to check if environment is ready

echo "════════════════════════════════════════════════════════════════"
echo "🧪 Sofia Pulse - Quick Environment Test"
echo "════════════════════════════════════════════════════════════════"
echo ""

ERRORS=0

# 1. Check Node.js
echo "📦 Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✅ Node.js installed: $NODE_VERSION"
else
    echo "   ❌ Node.js NOT found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. Check Python
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python installed: $PYTHON_VERSION"
else
    echo "   ❌ Python3 NOT found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Check pip
echo "📦 Checking pip..."
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
    echo "   ✅ pip installed: $PIP_VERSION"
else
    echo "   ⚠️  pip3 NOT found (optional but recommended)"
    echo "      Install: sudo apt install python3-pip -y"
fi
echo ""

# 4. Check PostgreSQL client
echo "🗄️  Checking PostgreSQL client..."
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | cut -d' ' -f3)
    echo "   ✅ psql installed: $PSQL_VERSION"
else
    echo "   ⚠️  psql NOT found (optional for manual DB access)"
    echo "      Install: sudo apt install postgresql-client -y"
fi
echo ""

# 5. Check npm packages
echo "📚 Checking npm packages..."
if [ -d "node_modules" ]; then
    PKG_COUNT=$(ls -1 node_modules | wc -l)
    echo "   ✅ node_modules found ($PKG_COUNT packages)"
else
    echo "   ❌ node_modules NOT found"
    echo "      Run: npm install"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 6. Check Python packages (psycopg2)
echo "📚 Checking Python packages..."
if python3 -c "import psycopg2" 2>/dev/null; then
    echo "   ✅ psycopg2 installed"
else
    echo "   ⚠️  psycopg2 NOT found"
    echo "      Install: pip3 install psycopg2-binary"
    echo "      Or: pip3 install -r requirements-collectors.txt"
fi
echo ""

# 7. Check .env file
echo "🔐 Checking .env configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file found"

    # Check key variables
    if grep -q "POSTGRES_HOST" .env; then
        echo "   ✅ POSTGRES_HOST configured"
    else
        echo "   ⚠️  POSTGRES_HOST not found in .env"
    fi

    if grep -q "POSTGRES_PASSWORD" .env; then
        echo "   ✅ POSTGRES_PASSWORD configured"
    else
        echo "   ⚠️  POSTGRES_PASSWORD not found in .env"
    fi
else
    echo "   ⚠️  .env file NOT found"
    echo "      Copy: cp .env.example .env"
fi
echo ""

# 8. Test PostgreSQL connection
echo "🔌 Testing PostgreSQL connection..."
if [ -f ".env" ]; then
    source .env 2>/dev/null || true

    DB_HOST="${POSTGRES_HOST:-localhost}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    DB_USER="${POSTGRES_USER:-sofia}"
    DB_NAME="${POSTGRES_DB:-sofia_db}"
    DB_PASS="${POSTGRES_PASSWORD}"

    if command -v psql &> /dev/null && [ -n "$DB_PASS" ]; then
        if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
            echo "   ✅ PostgreSQL connection OK"

            # Count tables
            TABLE_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia'" 2>/dev/null || echo "0")
            echo "   ℹ️  Tables in sofia schema: $TABLE_COUNT"
        else
            echo "   ❌ Cannot connect to PostgreSQL"
            echo "      Check if PostgreSQL is running: sudo systemctl status postgresql"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "   ⚠️  Cannot test connection (psql or password missing)"
    fi
else
    echo "   ⚠️  Skipping (no .env file)"
fi
echo ""

# 9. Check scripts permissions
echo "🔧 Checking scripts permissions..."
EXEC_COUNT=$(find scripts -name "*.py" -executable | wc -l)
TOTAL_COUNT=$(find scripts -name "*.py" | wc -l)
echo "   ℹ️  Executable scripts: $EXEC_COUNT / $TOTAL_COUNT"

if [ "$EXEC_COUNT" -lt "$TOTAL_COUNT" ]; then
    echo "   ⚠️  Some scripts are not executable"
    echo "      Fix: chmod +x scripts/*.py analytics/*.py"
fi
echo ""

# Final verdict
echo "════════════════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo "✅ ENVIRONMENT OK - Ready to run collectors!"
    echo ""
    echo "Next steps:"
    echo "  1. Choose collection option in FIXES-APPLIED.md"
    echo "  2. Run collectors: python3 scripts/collect-cepal-latam.py"
    echo "  3. Run analytics: python3 analytics/cross-data-correlations.py"
else
    echo "⚠️  FOUND $ERRORS CRITICAL ISSUE(S)"
    echo ""
    echo "Fix the issues above before running collectors."
fi
echo "════════════════════════════════════════════════════════════════"
