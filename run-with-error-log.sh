#!/bin/bash

# Sofia Pulse - Error Logger
# Captura erros do deployment e salva em arquivo

LOG_DIR="logs"
ERROR_LOG="$LOG_DIR/errors-$(date +%Y%m%d-%H%M%S).log"
SUMMARY_LOG="$LOG_DIR/latest-errors.txt"

mkdir -p "$LOG_DIR"

echo "🔍 Sofia Pulse - Error Analysis" > "$SUMMARY_LOG"
echo "Generated: $(date)" >> "$SUMMARY_LOG"
echo "" >> "$SUMMARY_LOG"

# Execute o script e capture todos os erros
bash RUN-EVERYTHING-AND-EMAIL.sh 2>&1 | tee "$ERROR_LOG" | grep -E "(Error|error|❌|⚠️|WARNING|FATAL)" > "$SUMMARY_LOG.tmp"

# Processar e categorizar erros
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
echo "CRITICAL ERRORS" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
grep -i "error\|fatal\|exception" "$SUMMARY_LOG.tmp" | sort -u >> "$SUMMARY_LOG"

echo "" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
echo "WARNINGS" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
grep "⚠️\|WARNING" "$SUMMARY_LOG.tmp" | sort -u >> "$SUMMARY_LOG"

echo "" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"
echo "FULL LOG: $ERROR_LOG" >> "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════" >> "$SUMMARY_LOG"

rm -f "$SUMMARY_LOG.tmp"

cat "$SUMMARY_LOG"
