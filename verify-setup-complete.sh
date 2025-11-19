#!/bin/bash

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔍 VERIFICAÇÃO COMPLETA - Sofia Pulse"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Detect environment
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
elif [ -d "/home/user/sofia-pulse" ]; then
    SOFIA_DIR="/home/user/sofia-pulse"
else
    echo "❌ Sofia Pulse directory not found!"
    exit 1
fi

cd "$SOFIA_DIR"

# 1. API Keys
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 🔑 API KEYS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f .env ]; then
    echo "✅ .env file found"
    echo ""

    # Check each key
    if grep -q "^EIA_API_KEY=QKUixUcUGW" .env; then
        echo "   ✅ EIA_API_KEY configured"
    else
        echo "   ❌ EIA_API_KEY not found or incorrect"
    fi

    if grep -q "^API_NINJAS_KEY=IsggR55vW5" .env; then
        echo "   ✅ API_NINJAS_KEY configured"
    else
        echo "   ❌ API_NINJAS_KEY not found or incorrect"
    fi

    if grep -q "^ALPHA_VANTAGE_API_KEY=JFVYRODTWGO1W5M6" .env; then
        echo "   ✅ ALPHA_VANTAGE_API_KEY configured"
    else
        echo "   ❌ ALPHA_VANTAGE_API_KEY not found or incorrect"
    fi
else
    echo "❌ .env file not found!"
    echo "   Run: ./setup-api-keys-final.sh"
fi

echo ""

# 2. Python Environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. 🐍 PYTHON ENVIRONMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -d "venv-analytics" ]; then
    echo "✅ venv-analytics found"

    # Check if packages are installed
    if [ -f "venv-analytics/bin/python3" ]; then
        source venv-analytics/bin/activate

        echo ""
        echo "   Checking packages..."
        python3 -c "import dotenv" 2>/dev/null && echo "   ✅ python-dotenv" || echo "   ❌ python-dotenv"
        python3 -c "import psycopg2" 2>/dev/null && echo "   ✅ psycopg2" || echo "   ❌ psycopg2"
        python3 -c "import pandas" 2>/dev/null && echo "   ✅ pandas" || echo "   ❌ pandas"
        python3 -c "import requests" 2>/dev/null && echo "   ✅ requests" || echo "   ❌ requests"

        deactivate
    fi
else
    echo "❌ venv-analytics not found!"
    echo "   Run: ./install-python-deps.sh"
fi

echo ""

# 3. Scripts
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. 📜 SCRIPTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SCRIPTS=(
    "setup-api-keys-final.sh"
    "setup-alpha-vantage.sh"
    "install-python-deps.sh"
    "run-all-with-venv.sh"
    "update-crontab-complete.sh"
    "verify-setup-complete.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        echo "   ✅ $script"
    elif [ -f "$script" ]; then
        echo "   ⚠️  $script (not executable)"
    else
        echo "   ❌ $script (not found)"
    fi
done

echo ""

# 4. Python Collectors
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. 🐍 PYTHON COLLECTORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

COLLECTORS=(
    "scripts/collect-electricity-consumption.py"
    "scripts/collect-port-traffic.py"
    "scripts/collect-commodity-prices.py"
    "scripts/collect-semiconductor-sales.py"
)

for collector in "${COLLECTORS[@]}"; do
    if [ -x "$collector" ]; then
        echo "   ✅ $collector"
    elif [ -f "$collector" ]; then
        echo "   ⚠️  $collector (not executable)"
    else
        echo "   ❌ $collector (not found)"
    fi
done

echo ""

# 5. Crontab
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. ⏰ CRONTAB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")

if [ -z "$CURRENT_CRONTAB" ]; then
    echo "❌ No crontab configured"
    echo "   Run: ./update-crontab-complete.sh"
else
    echo "✅ Crontab configured"
    echo ""

    # Count jobs
    TOTAL_JOBS=$(crontab -l | grep -v "^#" | grep -v "^$" | wc -l)
    echo "   Total jobs: $TOTAL_JOBS"
    echo ""

    # Check for Python collectors
    if crontab -l | grep -q "run-all-with-venv.sh"; then
        echo "   ✅ Python collectors scheduled"
        PYTHON_CRON=$(crontab -l | grep "run-all-with-venv.sh" | grep -v "^#")
        echo "      $PYTHON_CRON"
    else
        echo "   ❌ Python collectors NOT scheduled"
        echo "      Run: ./update-crontab-complete.sh"
    fi

    echo ""

    # Check for analytics
    if crontab -l | grep -q "run-all-now.sh"; then
        echo "   ✅ Analytics scheduled"
        ANALYTICS_CRON=$(crontab -l | grep "run-all-now.sh" | grep -v "^#")
        echo "      $ANALYTICS_CRON"
    else
        echo "   ⚠️  Analytics not found in crontab"
    fi
fi

echo ""

# 6. Database
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. 🗄️  DATABASE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Try to connect to database
if command -v psql &> /dev/null; then
    DB_PASSWORD=$(grep "^DB_PASSWORD=" .env 2>/dev/null | cut -d= -f2 || echo "sofia123strong")

    TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U sofia -d sofia_db -t -c "
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='sofia'
        AND table_name IN ('electricity_consumption', 'port_traffic', 'commodity_prices', 'semiconductor_sales')
        ORDER BY table_name;
    " 2>/dev/null | tr -d ' ')

    if [ -n "$TABLES" ]; then
        echo "✅ Database connected"
        echo ""
        echo "   Tables for Python collectors:"
        echo "$TABLES" | while read -r table; do
            if [ -n "$table" ]; then
                COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U sofia -d sofia_db -t -c "SELECT COUNT(*) FROM sofia.$table;" 2>/dev/null | tr -d ' ')
                echo "   ✅ $table ($COUNT records)"
            fi
        done
    else
        echo "⚠️  Database connected but tables not created"
        echo "   Run: python3 create-tables-python.py"
    fi
else
    echo "⚠️  psql not found, cannot verify database"
fi

echo ""

# 7. Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. 📋 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ALL_GOOD=true

# Check critical items
if [ ! -f .env ] || ! grep -q "^ALPHA_VANTAGE_API_KEY=JFVYRODTWGO1W5M6" .env; then
    echo "❌ Alpha Vantage API key not configured"
    echo "   Fix: ./setup-alpha-vantage.sh"
    ALL_GOOD=false
fi

if [ ! -d "venv-analytics" ]; then
    echo "❌ Python environment not set up"
    echo "   Fix: ./install-python-deps.sh"
    ALL_GOOD=false
fi

if [ -z "$CURRENT_CRONTAB" ] || ! echo "$CURRENT_CRONTAB" | grep -q "run-all-with-venv.sh"; then
    echo "❌ Crontab not configured for Python collectors"
    echo "   Fix: ./update-crontab-complete.sh"
    ALL_GOOD=false
fi

if [ "$ALL_GOOD" = true ]; then
    echo "✅ ALL SYSTEMS GO!"
    echo ""
    echo "🎯 Next execution:"
    echo "   Python Collectors: 13:00 UTC (10:00 BRT)"
    echo "   Analytics + Email: 22:00 UTC (19:00 BRT)"
else
    echo ""
    echo "⚠️  Some items need attention (see above)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
