#!/bin/bash
# Automatiza Sofia Pulse para rodar diariamente às 22:00 UTC (19:00 BRT)

echo "🔄 Configurando crontab..."

# Backup atual
crontab -l > /tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt 2>/dev/null || true

# Remover linha antiga (se existir)
crontab -l 2>/dev/null | grep -v "run-with-error-log.sh\|RUN-EVERYTHING-AND-EMAIL.sh" > /tmp/crontab-new.txt || echo "" > /tmp/crontab-new.txt

# Adicionar nova linha
echo "" >> /tmp/crontab-new.txt
echo "# Sofia Pulse - Coleta + Análise + Email (Seg-Sex 22:00 UTC / 19:00 BRT)" >> /tmp/crontab-new.txt
echo "0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-with-error-log.sh >> /var/log/sofia-pulse.log 2>&1" >> /tmp/crontab-new.txt

# Aplicar
crontab /tmp/crontab-new.txt

echo "✅ Crontab configurado!"
echo ""
echo "📅 Próxima execução: Seg-Sex às 22:00 UTC (19:00 BRT)"
echo "📧 Email será enviado para: augustosvm@gmail.com"
echo "📝 Logs em: /var/log/sofia-pulse.log"
echo ""
echo "Ver crontab: crontab -l"
