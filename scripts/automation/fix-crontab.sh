#!/bin/bash
# Remove linha duplicada do crontab

echo "🔧 Limpando crontab (removendo duplicatas)..."

# Backup
crontab -l > /tmp/crontab-backup-fix.txt

# Remover linhas antigas duplicadas (run-all-now.sh)
crontab -l | grep -v "run-all-now.sh" > /tmp/crontab-clean.txt

# Aplicar
crontab /tmp/crontab-clean.txt

echo "✅ Crontab limpo!"
echo ""
echo "📅 Agora roda APENAS 1x por dia:"
echo "   Seg-Sex às 22:00 UTC (19:00 BRT)"
echo "   Script: run-with-error-log.sh"
echo ""

# Verificar
echo "Linha instalada:"
crontab -l | grep "run-with-error-log.sh"
