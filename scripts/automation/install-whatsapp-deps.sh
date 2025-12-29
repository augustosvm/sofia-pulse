#!/bin/bash
# ============================================================================
# Install WhatsApp Integration Dependencies
# ============================================================================

set -e

echo "============================================================================"
echo "📦 INSTALLING WHATSAPP INTEGRATION DEPENDENCIES"
echo "============================================================================"
echo ""

# Activate venv if exists
if [ -d "venv-analytics" ]; then
    echo "🔄 Activating venv-analytics..."
    source venv-analytics/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  venv-analytics not found, using system Python"
fi

echo ""
echo "Installing Python packages..."

# Install python-dotenv (for loading .env files)
pip install -q python-dotenv

# Install requests (should already be installed, but just in case)
pip install -q requests

echo "✅ Dependencies installed"
echo ""

# Verify installation
echo "🔍 Verifying installation..."
python3 -c "import dotenv; import requests; print('✅ python-dotenv:', dotenv.__version__); print('✅ requests:', requests.__version__)"

echo ""
echo "============================================================================"
echo "✅ INSTALLATION COMPLETE"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Configure WhatsApp: bash setup-whatsapp-config.sh"
echo "  2. Test integration: bash test-sofia-whatsapp.sh"
echo ""
