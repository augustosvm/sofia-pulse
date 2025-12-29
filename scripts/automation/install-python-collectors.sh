#!/bin/bash

################################################################################
# Sofia Pulse - Install Python Collectors Dependencies
################################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "📦 INSTALLING PYTHON COLLECTORS DEPENDENCIES"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

echo "📦 Installing from requirements-collectors.txt..."
echo ""

pip3 install -r requirements-collectors.txt

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ INSTALLATION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Installed packages:"
echo "  ✅ psycopg2-binary (PostgreSQL)"
echo "  ✅ requests (HTTP)"
echo "  ✅ pandas (Data processing)"
echo "  ✅ numpy (Numeric operations)"
echo "  ✅ openpyxl (Excel files)"
echo ""
echo "You can now run the collectors:"
echo "  bash collect-fast-apis.sh"
echo "  bash collect-limited-apis-with-alerts.sh"
echo "  bash collect-international-orgs.sh"
echo ""
