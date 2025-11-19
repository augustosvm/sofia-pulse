#!/bin/bash

# Sofia Pulse - Error Logger
# Captura erros do deployment e salva em arquivo

LOG_DIR="logs"
ERROR_LOG="$LOG_DIR/errors-$(date +%Y%m%d-%H%M%S).log"
SUMMARY_LOG="$LOG_DIR/latest-errors.txt"

mkdir -p "$LOG_DIR"

# Execute o script e capture TUDO
echo "🚀 Executando RUN-EVERYTHING-AND-EMAIL.sh..."
echo ""
bash RUN-EVERYTHING-AND-EMAIL.sh 2>&1 | tee "$ERROR_LOG"

# Extrair erros do log completo
echo ""
echo "🔍 Analisando erros..."

# Criar summary
echo "🔍 Sofia Pulse - Error Analysis" > "$SUMMARY_LOG"
echo "Generated: $(date)" >> "$SUMMARY_LOG"
echo "" >> "$SUMMARY_LOG"

# Buscar padrões de erro (case insensitive)
grep -iE "error|exception|fatal|failed|traceback|errno|cannot|no such|not found|permission denied|connection refused" "$ERROR_LOG" > "$SUMMARY_LOG.tmp" 2>/dev/null || true

# Categorizar
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
echo "CRITICAL ERRORS" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"

if [ -s "$SUMMARY_LOG.tmp" ]; then
    grep -iE "error|exception|fatal|failed|traceback|errno" "$SUMMARY_LOG.tmp" | sort -u >> "$SUMMARY_LOG" || echo "(nenhum erro crítico)" >> "$SUMMARY_LOG"
else
    echo "(nenhum erro crítico)" >> "$SUMMARY_LOG"
fi

echo "" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
echo "WARNINGS" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"

grep -iE "warn|⚠️|cannot|no such|not found" "$ERROR_LOG" | sort -u >> "$SUMMARY_LOG" 2>/dev/null || echo "(nenhum warning)" >> "$SUMMARY_LOG"

echo "" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
echo "FULL LOG: $ERROR_LOG" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"

rm -f "$SUMMARY_LOG.tmp"

echo ""
echo "✅ Log salvo em: $SUMMARY_LOG"
echo ""
cat "$SUMMARY_LOG"
