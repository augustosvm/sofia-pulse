#!/bin/bash

################################################################################
# RUN EVERYTHING COMPLETE
# Setup + Coleta + Analytics + Email
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
echo "🚀 SOFIA PULSE - RUN EVERYTHING (COMPLETE)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Isso vai executar:"
echo "  0️⃣  Setup venv-analytics (se necessário)"
echo "  1️⃣  Fast APIs Collection (~5 min)"
echo "  2️⃣  Limited APIs Collection com Rate Limiter (~10-15 min)"
echo "  3️⃣  Analytics Generation (11 reports) (~3-5 min)"
echo "  4️⃣  Email Sending"
echo ""
echo "Tempo total estimado: ~25-30 minutos"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# 0. Setup venv (se não existir)
if [ ! -d "venv-analytics" ]; then
    echo "0️⃣  [$(date +%H:%M:%S)] Setup venv-analytics..."
    echo ""
    bash SETUP-ANALYTICS-COMPLETE.sh
    echo ""
    echo "   ✅ Setup Complete!"
    echo ""
else
    echo "0️⃣  [$(date +%H:%M:%S)] venv-analytics já existe - pulando setup"
    echo ""
fi

# 1. Fast APIs
echo "1️⃣  [$(date +%H:%M:%S)] Iniciando Fast APIs Collection..."
echo ""
bash collect-fast-apis.sh 2>&1 | tee /tmp/sofia-fast-apis.log
echo ""
echo "   ✅ Fast APIs Complete!"
echo ""

# 2. Limited APIs (com rate limiter)
echo "2️⃣  [$(date +%H:%M:%S)] Iniciando Limited APIs Collection (com rate limiter)..."
echo "   ⏳ Isso vai demorar ~10-15 min por causa dos delays de 60s"
echo ""
bash collect-limited-apis.sh 2>&1 | tee /tmp/sofia-limited-apis.log
echo ""
echo "   ✅ Limited APIs Complete!"
echo ""

# 3. Analytics
echo "3️⃣  [$(date +%H:%M:%S)] Gerando Analytics (11 reports)..."
echo ""
bash run-mega-analytics.sh 2>&1 | tee /tmp/sofia-analytics.log
echo ""
echo "   ✅ Analytics Complete!"
echo ""

# Contar quantos reports foram gerados
REPORTS_COUNT=$(ls -1 analytics/*-latest.txt 2>/dev/null | wc -l)
echo "   📊 Reports gerados: $REPORTS_COUNT"
ls -lh analytics/*-latest.txt 2>/dev/null | awk '{print "      - " $9 " (" $5 ")"}'
echo ""

# 4. Email
echo "4️⃣  [$(date +%H:%M:%S)] Enviando Email..."
echo ""
bash send-email-mega.sh 2>&1 | tee /tmp/sofia-email.log
echo ""
echo "   ✅ Email Sent!"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ COMPLETE RUN FINISHED!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📧 Verifique seu email em augustosvm@gmail.com"
echo ""
echo "📊 Relatórios gerados: $REPORTS_COUNT / 11"
echo ""
echo "🔍 Verificar melhorias de qualidade:"
echo "   - MEGA Analysis: Deve mostrar ~24 funding deals (não 4)"
echo "   - Tech Trend Score: Deve detectar 50+ frameworks (não 2)"
echo "   - Commodity Prices: Sem duplicações de Platinum/Copper"
echo "   - Special Sectors: Mais papers em Quantum Computing e Databases"
echo "   - NLG Playbooks: Recomendações mais específicas (se GEMINI_API_KEY configurado)"
echo ""
echo "🪵  Logs temporários em:"
echo "   /tmp/sofia-fast-apis.log"
echo "   /tmp/sofia-limited-apis.log"
echo "   /tmp/sofia-analytics.log"
echo "   /tmp/sofia-email.log"
echo ""
echo "🪵  Logs permanentes em:"
echo "   /var/log/sofia-fast-apis.log"
echo "   /var/log/sofia-limited-apis.log"
echo "   /var/log/sofia-analytics.log"
echo ""
