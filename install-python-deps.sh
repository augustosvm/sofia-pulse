#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "📦 INSTALLING PYTHON DEPENDENCIES"
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

# Check if venv exists
if [ -d "venv-analytics" ]; then
    echo "✅ Found existing venv-analytics"
    source venv-analytics/bin/activate
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv-analytics
    source venv-analytics/bin/activate
    echo "✅ Virtual environment created"
fi

echo ""
echo "📥 Installing core dependencies..."
pip install --upgrade pip

# Core dependencies
pip install python-dotenv
pip install psycopg2-binary
pip install requests
pip install pandas
pip install numpy

echo ""
echo "✅ Core dependencies installed!"
echo ""

# Verify
echo "🧪 Verifying installations..."
python3 -c "import dotenv; print('   ✅ python-dotenv')"
python3 -c "import psycopg2; print('   ✅ psycopg2')"
python3 -c "import requests; print('   ✅ requests')"
python3 -c "import pandas; print('   ✅ pandas')"
python3 -c "import numpy; print('   ✅ numpy')"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ SUCCESS! Python dependencies installed"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 To use, activate the virtual environment:"
echo ""
echo "   source venv-analytics/bin/activate"
echo ""
echo "📝 Or run scripts with venv:"
echo ""
echo "   venv-analytics/bin/python3 test-apis.py"
echo ""
