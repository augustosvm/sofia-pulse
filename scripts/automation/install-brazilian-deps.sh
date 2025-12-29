#!/bin/bash

echo "📦 Installing Brazilian APIs dependencies..."

# Activate venv
if [ -d "venv-analytics" ]; then
    source venv-analytics/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ venv-analytics not found"
    exit 1
fi

# Install psycopg2-binary (works without PostgreSQL dev headers)
pip install psycopg2-binary

echo ""
echo "✅ Dependencies installed"
echo ""
echo "You can now run: bash collect-brazilian-apis.sh"
