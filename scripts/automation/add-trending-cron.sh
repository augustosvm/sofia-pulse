#!/bin/bash
# Script para adicionar cron jobs dos novos caches (trending + AI mentions)

# Backup do crontab atual
crontab -l > /tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt

# Adicionar trending tech cache (3x/dia)
(crontab -l 2>/dev/null; echo "# Generate Trending Tech Cache (3x daily)") | crontab -
(crontab -l 2>/dev/null; echo "35 11 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-trending-cache.ts >> logs/trending-cache.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "35 15 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-trending-cache.ts >> logs/trending-cache.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "35 22 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-trending-cache.ts >> logs/trending-cache.log 2>&1") | crontab -

# Adicionar AI mentions cache (3x/dia)
(crontab -l 2>/dev/null; echo "# Generate AI Mentions Cache (3x daily)") | crontab -
(crontab -l 2>/dev/null; echo "40 11 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-ai-mentions-cache.ts >> logs/ai-mentions-cache.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "40 15 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-ai-mentions-cache.ts >> logs/ai-mentions-cache.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "40 22 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-ai-mentions-cache.ts >> logs/ai-mentions-cache.log 2>&1") | crontab -

echo "✅ Cron jobs adicionados:"
echo "  - Trending Tech: 11:35, 15:35, 22:35 UTC"
echo "  - AI Mentions: 11:40, 15:40, 22:40 UTC"

# Mostrar crontab atualizado
echo ""
echo "Crontab atual:"
crontab -l | grep -E "Trending|AI Mentions" -A1
