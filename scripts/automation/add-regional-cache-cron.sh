#!/bin/bash
# Script para adicionar cron job de atualização do cache regional
# Roda 3x por dia após as coletas de papers

# Backup do crontab atual
crontab -l > /tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt

# Adicionar 3 execuções diárias do generate-regional-cache
(crontab -l 2>/dev/null; echo "# Generate Regional Research Cache (3x daily)") | crontab -
(crontab -l 2>/dev/null; echo "30 11 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-regional-cache-v5-final.ts >> logs/regional-cache.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "30 15 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-regional-cache-v5-final.ts >> logs/regional-cache.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "30 22 * * * cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse && npx tsx scripts/generate-regional-cache-v5-final.ts >> logs/regional-cache.log 2>&1") | crontab -

echo "✅ Cron jobs adicionados:"
echo "  - 11:30 UTC (08:30 BRT) - Após coleta ArXiv/OpenAlex"
echo "  - 15:30 UTC (12:30 BRT) - Meio-dia"
echo "  - 22:30 UTC (19:30 BRT) - Noite"

# Mostrar crontab atualizado
echo ""
echo "Crontab atual:"
crontab -l | grep -A3 "Regional Research"
