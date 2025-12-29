#!/bin/bash
set -e

echo "============================================================================"
echo "🧹 SOFIA PULSE - Limpeza e Instalação de Crontab LIMPO"
echo "============================================================================"
echo ""

# Verificar se está no servidor correto
if [ ! -d "/home/ubuntu/sofia-pulse" ]; then
    echo "⚠️  ATENÇÃO: Este script deve ser executado no servidor em /home/ubuntu/sofia-pulse"
    echo ""
    echo "Se você está testando localmente, ignore este aviso."
    echo "Para instalar no servidor:"
    echo "  1. git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE"
    echo "  2. bash install-clean-crontab.sh"
    echo ""
    read -p "Continuar mesmo assim? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Backup do cron atual
echo "📦 1. Fazendo backup do crontab atual..."
BACKUP_FILE="$HOME/crontab-backup-$(date +%Y%m%d-%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No crontab found" > "$BACKUP_FILE"
echo "   ✅ Backup salvo em: $BACKUP_FILE"
echo ""

# 2. Criar novo crontab limpo
echo "🔧 2. Criando crontab LIMPO..."

# Definir diretório base
if [ -d "/home/ubuntu/sofia-pulse" ]; then
    SOFIA_DIR="/home/ubuntu/sofia-pulse"
else
    SOFIA_DIR="$(pwd)"
fi

cat > /tmp/sofia-crontab-clean.txt << EOF
# ============================================================================
# SOFIA PULSE - Cron Jobs (LIMPO - v2.0)
# ============================================================================
# Data da instalação: $(date)
# Branch: claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ============================================================================
# 1. COLLECTORS - Dados Reais
# ============================================================================

# Finance (B3, NASDAQ, Funding) - Seg-Sex às 21:00 UTC (18:00 BRT)
0 21 * * 1-5 cd $SOFIA_DIR && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1

# ArXiv AI Papers - Diário às 20:00 UTC
0 20 * * * cd $SOFIA_DIR && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1

# OpenAlex Papers - Diário às 20:05 UTC
5 20 * * * cd $SOFIA_DIR && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1

# AI Companies - Diário às 20:10 UTC
10 20 * * * cd $SOFIA_DIR && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1

# Patentes (WIPO China, EPO) - Diário às 01:00 UTC
0 1 * * * cd $SOFIA_DIR && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1

# IPOs Hong Kong - Seg-Sex às 02:00 UTC
0 2 * * 1-5 cd $SOFIA_DIR && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1

# NIH Grants (Biotech) - Semanal (segunda às 03:00 UTC)
0 3 * * 1 cd $SOFIA_DIR && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1

# Universidades Ásia - Mensal (dia 1 às 04:00 UTC)
0 4 1 * * cd $SOFIA_DIR && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1

# Cardboard Production (Leading Indicator) - Semanal (segunda às 05:00 UTC)
0 5 * * 1 cd $SOFIA_DIR && npm run collect:cardboard >> /var/log/sofia-cardboard.log 2>&1

# IPO Calendar (NASDAQ, B3, SEC/EDGAR) - Diário às 06:00 UTC
0 6 * * * cd $SOFIA_DIR && npm run collect:ipo-calendar >> /var/log/sofia-ipo.log 2>&1

# Jobs (Indeed, LinkedIn, AngelList) - Diário às 07:00 UTC
0 7 * * * cd $SOFIA_DIR && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# ============================================================================
# 2. INSIGHTS GENERATION (v2.0 - Com Análise Temporal!)
# ============================================================================

# Premium Insights v2.0 - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd $SOFIA_DIR && source venv-analytics/bin/activate && ./generate-insights-v2.0.sh >> /var/log/sofia-insights-v2.log 2>&1

# ============================================================================
# 3. EMAIL & REPORTING
# ============================================================================

# Email com Insights - Seg-Sex às 23:00 UTC (20:00 BRT)
0 23 * * 1-5 cd $SOFIA_DIR && ./send-insights-email.sh >> /var/log/sofia-email.log 2>&1

# ============================================================================
# 4. BACKUPS (mantidos do cron original)
# ============================================================================

# Auto-recovery (a cada 1 minuto)
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh

# Backups diversos
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh

# Sofia Pulse backup
0 4 * * * cd $SOFIA_DIR && ./scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1

# ============================================================================
# TOTAL: 16 collectors + 2 insights/email + 5 backups = 23 jobs
# ============================================================================
#
# REMOVIDO (não existem):
#   - collect-cron.sh
#   - cron-daily.sh
#   - cron-weekly.sh
#   - cron-monthly.sh
#   - npm run collect:yc
#   - npm run collect:sec
#   - npm run collect:hackernews
#
# ADICIONADO (existiam mas não estavam no cron):
#   - collect:arxiv-ai
#   - collect:openalex
#   - collect:ai-companies
#   - collect:patents-all (wipo-china + epo)
#   - collect:hkex
#   - collect:nih-grants
#   - collect:asia-universities
#   - collect:cardboard
#   - collect:ipo-calendar (novo!)
#   - collect:jobs (novo!)
#
# CORRIGIDO:
#   - Removidas 3x linhas duplicadas de generate-insights.sh
#   - Trocado generate-insights.sh (v1.0) por generate-insights-v2.0.sh (v2.0)
# ============================================================================
EOF

echo "   ✅ Crontab limpo criado em: /tmp/sofia-crontab-clean.txt"
echo ""

# 3. Mostrar diff (o que vai mudar)
echo "📊 3. Comparando cron ATUAL vs NOVO..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
diff -u "$BACKUP_FILE" /tmp/sofia-crontab-clean.txt || true
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Perguntar confirmação
echo "🚨 4. REVISÃO DAS MUDANÇAS:"
echo ""
echo "   ✅ ADICIONADOS: 11 collectors que existiam mas não rodavam"
echo "   ❌ REMOVIDOS: 7 linhas com scripts inexistentes"
echo "   ❌ REMOVIDOS: 3 linhas duplicadas (generate-insights.sh)"
echo "   🔄 ATUALIZADO: generate-insights.sh → generate-insights-v2.0.sh"
echo ""
echo "   Backup do cron atual: $BACKUP_FILE"
echo ""
read -p "Deseja instalar o novo crontab? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Instalação cancelada."
    echo "   O crontab limpo está em: /tmp/sofia-crontab-clean.txt"
    echo "   Para instalar manualmente: crontab /tmp/sofia-crontab-clean.txt"
    exit 0
fi

# 5. Instalar novo crontab
echo ""
echo "⚙️  5. Instalando novo crontab..."
crontab /tmp/sofia-crontab-clean.txt

echo "   ✅ Crontab instalado com sucesso!"
echo ""

# 6. Verificar instalação
echo "🔍 6. Verificando instalação..."
echo ""
crontab -l | grep -E "^[^#]" | head -15
echo "   ..."
echo ""

# 7. Verificar logs
echo "📁 7. Criando diretórios de log (se necessário)..."
sudo mkdir -p /var/log
sudo touch /var/log/sofia-{finance,arxiv,openalex,ai-companies,patents,hkex,nih,unis,cardboard,ipo,jobs,insights-v2,email,backup}.log
sudo chown $USER:$USER /var/log/sofia-*.log 2>/dev/null || true
echo "   ✅ Logs prontos"
echo ""

# 8. Resumo final
echo "============================================================================"
echo "✅ INSTALAÇÃO CONCLUÍDA!"
echo "============================================================================"
echo ""
echo "📊 Estatísticas do novo cron:"
echo "   • 11 collectors de dados (finance, AI, patents, etc)"
echo "   • 2 insights + email (v2.0 com análise temporal)"
echo "   • 5 backups (mantidos do cron original)"
echo "   • 5 scripts inexistentes removidos"
echo "   • 3 duplicatas removidas"
echo ""
echo "📁 Arquivos importantes:"
echo "   • Backup anterior: $BACKUP_FILE"
echo "   • Crontab limpo: /tmp/sofia-crontab-clean.txt"
echo "   • Logs: /var/log/sofia-*.log"
echo ""
echo "🔍 Para verificar se está funcionando:"
echo "   • Ver cron atual: crontab -l"
echo "   • Ver logs: tail -f /var/log/sofia-*.log"
echo "   • Testar collector: npm run collect:arxiv-ai"
echo "   • Testar insights v2.0: ./generate-insights-v2.0.sh"
echo ""
echo "📅 Próximas execuções:"
echo "   • 20:00 UTC - ArXiv, OpenAlex, AI Companies"
echo "   • 21:00 UTC - Finance (B3, NASDAQ, Funding)"
echo "   • 22:00 UTC - Premium Insights v2.0"
echo "   • 23:00 UTC - Email com insights + CSVs"
echo ""
echo "============================================================================"
