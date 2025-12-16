#!/bin/bash
# Adicionar coletores de vagas ao crontab atual

(crontab -l 2>/dev/null; cat << 'EOF'

# ============================================================
# COLETORES DE VAGAS - 3x por dia
# ============================================================

# 10:00 BRT (13:00 UTC) - Manhã
0 13 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-morning.log 2>&1

# 15:00 BRT (18:00 UTC) - Tarde
0 18 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-afternoon.log 2>&1

# 18:00 BRT (21:00 UTC) - Noite
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-jobs-collectors.sh >> /var/log/sofia/jobs-evening.log 2>&1

EOF
) | crontab -

echo "✅ Coletores de vagas adicionados!"
echo ""
echo "Verificando..."
crontab -l | grep -A2 "COLETORES DE VAGAS"
