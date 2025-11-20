#!/bin/bash

################################################################################
# SETUP COMPLETO - Analytics venv + Todas as Dependências
################################################################################

set -e

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

echo "════════════════════════════════════════════════════════════════"
echo "📦 SETUP COMPLETO - Analytics"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Criar venv-analytics
echo "1️⃣  Criando virtual environment..."
echo ""

if [ -d "venv-analytics" ]; then
    echo "   ⚠️  venv-analytics já existe - removendo..."
    rm -rf venv-analytics
fi

python3 -m venv venv-analytics
source venv-analytics/bin/activate

echo "   ✅ Virtual environment criado"
echo ""

# 2. Atualizar pip
echo "2️⃣  Atualizando pip..."
pip install --upgrade pip --quiet
echo "   ✅ pip atualizado"
echo ""

# 3. Instalar dependências CORE
echo "3️⃣  Instalando dependências CORE..."
echo ""

pip install --quiet python-dotenv
echo "   ✅ python-dotenv"

pip install --quiet psycopg2-binary
echo "   ✅ psycopg2-binary"

pip install --quiet requests
echo "   ✅ requests"

pip install --quiet pandas
echo "   ✅ pandas"

pip install --quiet numpy
echo "   ✅ numpy"

echo ""

# 4. Instalar dependências ML/ANALYTICS
echo "4️⃣  Instalando dependências ML/ANALYTICS..."
echo ""

pip install --quiet scikit-learn
echo "   ✅ scikit-learn (sklearn)"

pip install --quiet scipy
echo "   ✅ scipy"

pip install --quiet fuzzywuzzy
echo "   ✅ fuzzywuzzy"

pip install --quiet python-Levenshtein
echo "   ✅ python-Levenshtein"

echo ""

# 5. Instalar dependências AI (opcional)
echo "5️⃣  Instalando dependências AI (opcional)..."
echo ""

pip install --quiet google-generativeai || echo "   ⚠️  google-generativeai skipped"
echo "   ✅ google-generativeai"

echo ""

# 6. Verificar instalações
echo "6️⃣  Verificando instalações..."
echo ""

python3 -c "import dotenv; print('   ✅ python-dotenv')"
python3 -c "import psycopg2; print('   ✅ psycopg2')"
python3 -c "import requests; print('   ✅ requests')"
python3 -c "import pandas; print('   ✅ pandas')"
python3 -c "import numpy; print('   ✅ numpy')"
python3 -c "import sklearn; print('   ✅ scikit-learn')"
python3 -c "import scipy; print('   ✅ scipy')"
python3 -c "import fuzzywuzzy; print('   ✅ fuzzywuzzy')"
python3 -c "import Levenshtein; print('   ✅ python-Levenshtein')"
python3 -c "import google.generativeai; print('   ✅ google-generativeai')" || echo "   ⚠️  google-generativeai (opcional)"

echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETO!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Virtual environment criado em:"
echo "   venv-analytics/"
echo ""
echo "📝 Para ativar manualmente:"
echo "   source venv-analytics/bin/activate"
echo ""
echo "📝 Próximos passos:"
echo "   bash run-mega-analytics.sh"
echo "   bash send-email-mega.sh"
echo ""
