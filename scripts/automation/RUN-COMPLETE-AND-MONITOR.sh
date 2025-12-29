#!/bin/bash

################################################################################
# RUN COMPLETE: Collection + Analytics + Email (Com Monitoring)
################################################################################

set -e

cd ~/sofia-pulse

echo "════════════════════════════════════════════════════════════════"
echo "🚀 SOFIA PULSE - COMPLETE RUN"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Isso vai executar:"
echo "  1️⃣  Fast APIs Collection (~5 min)"
echo "  2️⃣  Limited APIs Collection com Rate Limiter (~10-15 min)"
echo "  3️⃣  Analytics Generation (~3-5 min)"
echo "  4️⃣  Email Sending"
echo ""
echo "Tempo total estimado: ~20-25 minutos"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Fast APIs
echo "1️⃣  [$(date +%H:%M:%S)] Iniciando Fast APIs Collection..."
echo ""
bash collect-fast-apis.sh
echo ""
echo "   ✅ Fast APIs Complete!"
echo ""

# 2. Limited APIs (com rate limiter)
echo "2️⃣  [$(date +%H:%M:%S)] Iniciando Limited APIs Collection (com rate limiter)..."
echo "   ⏳ Isso vai demorar ~10-15 min por causa dos delays de 60s"
echo ""
bash collect-limited-apis.sh
echo ""
echo "   ✅ Limited APIs Complete!"
echo ""

# 3. Analytics
echo "3️⃣  [$(date +%H:%M:%S)] Gerando Analytics (11 reports)..."
echo ""
bash run-mega-analytics.sh
echo ""
echo "   ✅ Analytics Complete!"
echo ""

# 4. Email
echo "4️⃣  [$(date +%H:%M:%S)] Enviando Email..."
echo ""
bash send-email-mega.sh
echo ""
echo "   ✅ Email Sent!"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ COMPLETE RUN FINISHED!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📧 Verifique seu email em augustosvm@gmail.com"
echo ""
echo "📊 Você deve receber:"
echo "   - 11 arquivos TXT (relatórios)"
echo "   - 15+ arquivos CSV (dados brutos)"
echo ""
echo "🔍 Verificar melhorias de qualidade:"
echo "   - MEGA Analysis: ~24 funding deals (não 4)"
echo "   - Tech Trend Score: 50+ frameworks (não 2)"
echo "   - Commodity Prices: Sem duplicações"
echo "   - Special Sectors: Mais papers em Quantum/Databases"
echo "   - NLG Playbooks: Recomendações mais específicas"
echo ""
echo "🪵  Logs em:"
echo "   /var/log/sofia-fast-apis.log"
echo "   /var/log/sofia-limited-apis.log"
echo "   /var/log/sofia-analytics.log"
echo ""
