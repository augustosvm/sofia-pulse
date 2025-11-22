#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "📱 PRÓXIMAS NOTIFICAÇÕES WHATSAPP AUTOMÁTICAS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Current time
now_utc=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
now_brt=$(TZ='America/Sao_Paulo' date +"%Y-%m-%d %H:%M:%S BRT")

echo "⏰ Agora:"
echo "   UTC: $now_utc"
echo "   BRT: $now_brt"
echo ""

# Current hour and day
current_hour_utc=$(date -u +%H)
current_day=$(date +%u)  # 1-7 (Mon-Sun)

echo "════════════════════════════════════════════════════════════════"
echo "📅 SCHEDULE CONFIGURADO:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "☀️  16:00 UTC (13:00 BRT) - Segunda a Sexta"
echo "   📱 WhatsApp: Resumo da coleta de APIs"
echo "   • Total de collectors executados"
echo "   • Quais falharam (se houver)"
echo ""
echo "🌙 22:00 UTC (19:00 BRT) - Segunda a Sexta"
echo "   📱 WhatsApp 1: Resumo dos 23 relatórios de analytics"
echo "   📱 WhatsApp 2: Confirmação de envio de email (5 min depois)"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "⏰ PRÓXIMA NOTIFICAÇÃO:"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Calculate next notification
if [ "$current_day" -ge 1 ] && [ "$current_day" -le 5 ]; then
    # Weekday
    if [ "$current_hour_utc" -lt 16 ]; then
        hours_until=$((16 - current_hour_utc))
        echo "📱 HOJE às 16:00 UTC (13:00 BRT)"
        echo "   Em ~$hours_until horas"
        echo ""
        echo "   Você vai receber:"
        echo "   ✅ Resumo da coleta de APIs limitadas"
        echo "   📊 Total de collectors: 10"
        echo "   ✅ Sucessos vs ❌ Falhas"
        echo ""
    elif [ "$current_hour_utc" -lt 22 ]; then
        hours_until=$((22 - current_hour_utc))
        echo "📱 HOJE às 22:00 UTC (19:00 BRT)"
        echo "   Em ~$hours_until horas"
        echo ""
        echo "   Você vai receber:"
        echo "   1. ✅ Resumo dos 23 analytics (22:00)"
        echo "   2. ✅ Confirmação de email enviado (22:05)"
        echo ""
    else
        echo "📱 AMANHÃ às 16:00 UTC (13:00 BRT)"
        hours_until=$((24 - current_hour_utc + 16))
        echo "   Em ~$hours_until horas"
        echo ""
        echo "   Você vai receber:"
        echo "   ✅ Resumo da coleta de APIs limitadas"
        echo ""
    fi
else
    # Weekend - next Monday
    days_until=$((8 - current_day))
    echo "📱 SEGUNDA-FEIRA às 16:00 UTC (13:00 BRT)"
    echo "   Em ~$days_until dias"
    echo ""
    echo "   Você vai receber:"
    echo "   ✅ Resumo da coleta de APIs limitadas"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 DICA: Para testar AGORA sem esperar:"
echo ""
echo "   # Testar coleta com alertas"
echo "   bash collect-limited-apis-with-alerts.sh"
echo ""
echo "   # Testar analytics com alertas"
echo "   bash run-mega-analytics-with-alerts.sh"
echo ""
echo "   # Testar envio de email"
echo "   bash send-email-mega.sh"
echo ""
