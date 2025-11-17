#!/bin/bash

echo "🔍 Verificando Crontab - Sofia Pulse"
echo "===================================="
echo ""

echo "📋 Crontab do usuário atual:"
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "  (vazio ou não encontrado)"

echo ""
echo "📋 Crontab do root:"
sudo crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "  (vazio ou não encontrado)"

echo ""
echo "📋 Arquivos em /etc/cron.d/:"
ls -la /etc/cron.d/ 2>/dev/null | grep sofia || echo "  (nenhum arquivo sofia encontrado)"

echo ""
echo "📋 Arquivos em /etc/cron.daily/:"
ls -la /etc/cron.daily/ 2>/dev/null | grep sofia || echo "  (nenhum arquivo sofia encontrado)"

echo ""
echo "📋 Processos cron rodando:"
ps aux | grep cron | grep -v grep

echo ""
echo "✅ Verificação completa!"
