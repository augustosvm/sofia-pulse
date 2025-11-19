#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔄 ATUALIZANDO CRONTAB - Sofia Pulse"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Backup do crontab atual
BACKUP_FILE="/tmp/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
echo "📋 Fazendo backup do crontab atual..."
crontab -l > "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

# Criar novo crontab removendo linhas antigas
echo "🔧 Removendo linhas antigas..."
crontab -l | grep -v "generate-insights-complete.sh" | grep -v "send-insights-email-complete.sh" > /tmp/crontab-new.txt

# Adicionar nova linha manualmente
echo "➕ Adicionando nova linha..."
cat > /tmp/crontab-insert.txt << 'CRONEOF'

# ============================================================================
# INSIGHTS GENERATION + EMAIL (UNIFICADO!)
# ============================================================================

# Run ALL: Migrations + Coleta + Análises + Email - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-all-now.sh >> /var/log/sofia-pulse-complete.log 2>&1

# ============================================================================
# EMAIL & REPORTING
# ============================================================================

# (Email enviado automaticamente pelo run-all-now.sh acima)
CRONEOF

# Juntar tudo
cat > /tmp/crontab-final.txt << 'EOF'
# ============================================================================
# DATA COLLECTION - Sofia Pulse
# ============================================================================

# GitHub Trending - Diariamente às 8:00 UTC
0 8 * * * cd /home/ubuntu/sofia-pulse && npm run collect:github-trending >> /var/log/sofia-github.log 2>&1

# HackerNews - Diariamente às 8:30 UTC
30 8 * * * cd /home/ubuntu/sofia-pulse && npm run collect:hackernews >> /var/log/sofia-hn.log 2>&1

# Finance - Seg-Sex às 21:00 UTC
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1

# ArXiv AI - Diariamente às 20:00 UTC
0 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1

# OpenAlex - Diariamente às 20:05 UTC
5 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1

# AI Companies - Diariamente às 20:10 UTC
10 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1

# Patents - Diariamente às 1:00 UTC
0 1 * * * cd /home/ubuntu/sofia-pulse && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1

# HKEX - Seg-Sex às 2:00 UTC
0 2 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1

# NIH Grants - Segundas às 3:00 UTC
0 3 * * 1 cd /home/ubuntu/sofia-pulse && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1

# Asia Universities - Dia 1 de cada mês às 4:00 UTC
0 4 1 * * cd /home/ubuntu/sofia-pulse && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1

# Cardboard - Segundas às 5:00 UTC
0 5 * * 1 cd /home/ubuntu/sofia-pulse && npm run collect:cardboard >> /var/log/sofia-cardboard.log 2>&1

# IPO Calendar - Diariamente às 6:00 UTC
0 6 * * * cd /home/ubuntu/sofia-pulse && npm run collect:ipo-calendar >> /var/log/sofia-ipo.log 2>&1

# Jobs - Diariamente às 7:00 UTC
0 7 * * * cd /home/ubuntu/sofia-pulse && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# ============================================================================
# INSIGHTS GENERATION + EMAIL (UNIFICADO!)
# ============================================================================

# Run ALL: Migrations + Coleta + Análises + Email - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-all-now.sh >> /var/log/sofia-pulse-complete.log 2>&1

# ============================================================================
# EMAIL & REPORTING
# ============================================================================

# (Email enviado automaticamente pelo run-all-now.sh acima)

# ============================================================================
# BACKUPS
# ============================================================================

# Auto-recovery
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh 2>/dev/null || true

# Backups diversos
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh 2>/dev/null || true
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh 2>/dev/null || true
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh 2>/dev/null || true

# Sofia backup
0 4 * * * cd /home/ubuntu/sofia-pulse && ./scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1 || true

# ============================================================================
# TOTAL: 13 collectors + 1 insights/email + 5 backups = 19 jobs
# ============================================================================
EOF

echo "✅ Novo crontab criado"
echo ""

echo "════════════════════════════════════════════════════════════════════════════════"
echo "📄 PREVIEW - MUDANÇAS:"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "❌ REMOVIDO:"
echo "   0 22 * * 1-5 ... generate-insights-complete.sh"
echo "   0 23 * * 1-5 ... send-insights-email-complete.sh"
echo ""
echo "✅ ADICIONADO:"
echo "   0 22 * * 1-5 ... bash run-all-now.sh"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Aplicar este crontab? (y/n) " -n 1 -r
echo ""
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✅ Aplicando novo crontab..."
    crontab /tmp/crontab-final.txt

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "✅ CRONTAB ATUALIZADO COM SUCESSO!"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "🎯 PRÓXIMA EXECUÇÃO: 22:00 UTC / 19:00 BRT (Seg-Sex)"
    echo ""
    echo "   O que vai acontecer:"
    echo "   1. Migrations no banco"
    echo "   2. Coleta de dados (Reddit, NPM, PyPI, etc)"
    echo "   3. Análises completas (Top 10, Correlações, Dark Horses, etc)"
    echo "   4. Email para augustosvm@gmail.com"
    echo ""
    echo "   Log: /var/log/sofia-pulse-complete.log"
    echo ""
    echo "Comandos úteis:"
    echo "   crontab -l | grep run-all-now.sh    # Ver job instalado"
    echo "   tail -f /var/log/sofia-pulse-complete.log    # Acompanhar execução"
    echo ""
    echo "Backup salvo em: $BACKUP_FILE"
    echo ""
else
    echo "❌ Cancelado"
    echo ""
    echo "Para aplicar manualmente:"
    echo "   crontab /tmp/crontab-final.txt"
    echo ""
    echo "Para restaurar backup:"
    echo "   crontab $BACKUP_FILE"
    echo ""
fi
