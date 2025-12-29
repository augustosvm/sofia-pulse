#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "📅 APLICANDO CRONTAB ATUALIZADO"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

SOFIA_DIR="/home/ubuntu/sofia-pulse"
[ -d "$SOFIA_DIR" ] || SOFIA_DIR="$(pwd)"
cd "$SOFIA_DIR"

if [ ! -f "crontab-updated.txt" ]; then
    echo "❌ Arquivo crontab-updated.txt não encontrado"
    exit 1
fi

echo "📋 Conteúdo do novo crontab:"
echo ""
cat crontab-updated.txt
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Deseja aplicar este crontab? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✅ Aplicando crontab..."
    crontab crontab-updated.txt

    echo ""
    echo "✅ Crontab aplicado com sucesso!"
    echo ""
    echo "📋 Verificando jobs instalados:"
    crontab -l | grep -E "(sofia|SOFIA)" || echo "  Nenhum job encontrado"
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "✅ PRÓXIMA EXECUÇÃO:"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "   22:00 UTC (19:00 BRT) - Análises completas + Email"
    echo ""
    echo "   Logs disponíveis em:"
    echo "   - /var/log/sofia-pulse-complete.log (execução principal)"
    echo "   - /var/log/sofia-*.log (collectors individuais)"
    echo ""
else
    echo "❌ Cancelado. Para aplicar manualmente:"
    echo "   crontab crontab-updated.txt"
    echo ""
fi
