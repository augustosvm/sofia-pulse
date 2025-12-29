#!/bin/bash

#============================================================================
# Sofia Pulse - Data Mining & AI Insights Setup
#============================================================================
# Instala todas as ferramentas para:
# - Data mining
# - Correlation analysis
# - Clustering
# - Anomaly detection
# - Google Gemini AI insights (barato!)
#============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔬 Sofia Pulse - Data Mining & AI Insights Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd ~/sofia-pulse

# Ativar venv (ou criar se não existir)
if [ ! -d "venv-analytics" ]; then
  echo "📦 Criando ambiente virtual..."
  python3 -m venv venv-analytics
fi

echo "🔌 Ativando venv..."
source venv-analytics/bin/activate

echo ""
echo "📥 Instalando ferramentas de Data Mining..."
echo ""

# Core data science stack
echo "1️⃣  Instalando Pandas, NumPy, SciPy..."
pip install pandas numpy scipy

# Machine Learning & Data Mining
echo "2️⃣  Instalando Scikit-learn (ML, clustering, correlations)..."
pip install scikit-learn

# Visualizações
echo "3️⃣  Instalando Matplotlib, Seaborn, Plotly..."
pip install matplotlib seaborn plotly

# Database
echo "4️⃣  Instalando conectores PostgreSQL..."
pip install psycopg2-binary sqlalchemy

# Jupyter
echo "5️⃣  Instalando Jupyter Lab..."
pip install jupyterlab ipywidgets

# AI Insights (Gemini - MUITO mais barato que Claude API)
echo "6️⃣  Instalando Google Gemini SDK..."
pip install google-generativeai

# EDA Automático (100% grátis, sem precisar de IA!)
echo "6.5️⃣  Instalando ferramentas de EDA automático..."
pip install ydata-profiling sweetviz dtale

# Statistical analysis
echo "7️⃣  Instalando ferramentas estatísticas..."
pip install statsmodels

# Time series analysis
echo "8️⃣  Instalando Prophet (time series forecasting)..."
pip install prophet

# Extras úteis
echo "9️⃣  Instalando utilities..."
pip install python-dotenv tqdm

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Instalação Completa!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Ferramentas Instaladas:"
echo ""
echo "  Data Mining:"
echo "    ✅ Pandas - Análise de dados"
echo "    ✅ NumPy - Computação numérica"
echo "    ✅ SciPy - Análises estatísticas"
echo "    ✅ Scikit-learn - Machine Learning"
echo ""
echo "  Visualização:"
echo "    ✅ Matplotlib - Gráficos básicos"
echo "    ✅ Seaborn - Gráficos estatísticos"
echo "    ✅ Plotly - Gráficos interativos"
echo ""
echo "  EDA Automático (GRÁTIS!):"
echo "    ✅ Pandas Profiling - Relatórios HTML completos"
echo "    ✅ Sweetviz - Comparações automáticas"
echo "    ✅ D-Tale - Dashboard interativo"
echo ""
echo "  AI & Analysis:"
echo "    ✅ Google Gemini - AI insights (BARATO!)"
echo "    ✅ Statsmodels - Estatística avançada"
echo "    ✅ Prophet - Time series forecasting"
echo ""
echo "  Database:"
echo "    ✅ PostgreSQL connectors"
echo "    ✅ SQLAlchemy ORM"
echo ""
echo "  Interface:"
echo "    ✅ Jupyter Lab - Notebooks interativos"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Próximo Passo:"
echo ""
echo "   1. Configure sua API key do Gemini no .env:"
echo "      echo 'GEMINI_API_KEY=sua_key_aqui' >> ~/.env"
echo "      (Grátis: https://aistudio.google.com/app/apikey)"
echo ""
echo "   2. Inicie o Jupyter Lab:"
echo "      source ~/sofia-pulse/venv-analytics/bin/activate"
echo "      jupyter lab --ip=0.0.0.0 --port=8888 --no-browser"
echo ""
echo "   3. Abra o notebook de Data Mining:"
echo "      http://seu-servidor:8888"
echo "      Abra: analytics/notebooks/data-mining-insights.ipynb"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
