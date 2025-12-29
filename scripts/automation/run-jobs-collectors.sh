#!/bin/bash
# Script para executar todos os coletores de vagas
# Autor: Sofia Pulse
# Data: 2025-12-10

cd /home/ubuntu/sofia-pulse || exit 1

echo "======================================================================"
echo "SOFIA PULSE - Coleta de Vagas Tech"
echo "Iniciado em: $(date)"
echo "======================================================================"

# Enviar notificação WhatsApp de início
python3 -c "
from scripts.utils.whatsapp_alerts import send_whatsapp_info
send_whatsapp_info('🚀 Iniciando coleta de vagas - $(date +%H:%M)')
" 2>/dev/null || echo "WhatsApp notification skipped"

# Ativar venv se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

TOTAL_COLLECTED=0

# Lista de coletores (APIs públicas, sem necessidade de chaves)
COLLECTORS=(
    "scripts/collect-jobs-arbeitnow.ts"
    "scripts/collect-jobs-themuse.ts"
    "scripts/collect-jobs-github.ts"
    "scripts/collect-jobs-himalayas.ts"
    "scripts/collect-jobs-weworkremotely.ts"
)

for collector in "${COLLECTORS[@]}"; do
    if [ -f "$collector" ]; then
        echo ""
        echo "----------------------------------------------------------------------"
        echo "Executando: $collector"
        echo "----------------------------------------------------------------------"
        
        # Executar com node --import tsx (Node 20+)
        if node --import tsx "$collector" 2>&1; then
            echo "✅ $collector concluído com sucesso"
        else
            echo "❌ $collector falhou"
        fi
    else
        echo "⚠️  Arquivo não encontrado: $collector"
    fi
done

# Contar total de vagas
TOTAL_JOBS=$(npx tsx -e "
import { Client } from 'pg';
import dotenv from 'dotenv';
dotenv.config();
const client = new Client({
    host: process.env.POSTGRES_HOST,
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER,
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB
});
client.connect().then(() => 
    client.query('SELECT COUNT(*) as total FROM sofia.jobs')
).then(r => {
    console.log(r.rows[0].total);
    client.end();
}).catch(() => console.log('0'));
" 2>/dev/null || echo "0")

echo ""
echo "======================================================================"
echo "Coleta finalizada em: $(date)"
echo "📊 Total de vagas no banco: $TOTAL_JOBS"
echo "======================================================================"

# Enviar notificação WhatsApp de conclusão
python3 -c "
from scripts.utils.whatsapp_alerts import send_whatsapp_info
message = '''✅ Coleta de vagas concluída!

📊 Total no banco: $TOTAL_JOBS vagas
⏰ Finalizado: $(date +%H:%M)'''
send_whatsapp_info(message)
" 2>/dev/null || echo "WhatsApp notification skipped"
