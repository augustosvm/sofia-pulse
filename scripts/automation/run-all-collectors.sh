#!/bin/bash
# Script master para executar TODOS os coletores de vagas
# Executa em background e salva logs

LOG_FILE="/var/log/sofia-jobs-collection.log"

echo "========================================" | tee -a $LOG_FILE
echo "🚀 INICIANDO COLETA COMPLETA DE VAGAS" | tee -a $LOG_FILE
echo "$(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

cd /home/ubuntu/sofia-pulse
source venv/bin/activate

# Contadores
TOTAL_ANTES=$(python3 -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); c = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT', '5432'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), database=os.getenv('POSTGRES_DB')); cur = c.cursor(); cur.execute('SELECT COUNT(*) FROM sofia.jobs'); print(cur.fetchone()[0]); c.close()")

echo "📊 Total ANTES: $TOTAL_ANTES vagas" | tee -a $LOG_FILE

# APIs Premium (com timeout de 2 minutos cada)
echo "🔥 Executando APIs Premium..." | tee -a $LOG_FILE
timeout 120 python3 scripts/collect-rapidapi-activejobs.py >> $LOG_FILE 2>&1
timeout 120 python3 scripts/collect-rapidapi-linkedin.py >> $LOG_FILE 2>&1
timeout 120 python3 scripts/collect-serpapi-googlejobs.py >> $LOG_FILE 2>&1
timeout 120 python3 scripts/collect-theirstack-api.py >> $LOG_FILE 2>&1

# APIs Gratuitas (com timeout de 3 minutos)
echo "🆓 Executando APIs Gratuitas..." | tee -a $LOG_FILE
timeout 180 node --import tsx scripts/collect-jobs-free-apis.ts >> $LOG_FILE 2>&1

# Coletores Específicos (com timeout de 2 minutos cada)
echo "🎯 Executando Coletores Específicos..." | tee -a $LOG_FILE
timeout 120 python3 scripts/collect-focused-areas.py >> $LOG_FILE 2>&1
timeout 120 python3 scripts/collect-himalayas-api.py >> $LOG_FILE 2>&1

# Total final
TOTAL_DEPOIS=$(python3 -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); c = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT', '5432'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), database=os.getenv('POSTGRES_DB')); cur = c.cursor(); cur.execute('SELECT COUNT(*) FROM sofia.jobs'); print(cur.fetchone()[0]); c.close()")

NOVAS=$((TOTAL_DEPOIS - TOTAL_ANTES))

echo "========================================" | tee -a $LOG_FILE
echo "✅ COLETA CONCLUÍDA!" | tee -a $LOG_FILE
echo "📊 Total ANTES: $TOTAL_ANTES vagas" | tee -a $LOG_FILE
echo "📊 Total DEPOIS: $TOTAL_DEPOIS vagas" | tee -a $LOG_FILE
echo "🆕 Novas vagas: $NOVAS" | tee -a $LOG_FILE
echo "$(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

# Mostrar resumo por plataforma
python3 scripts/simple-check.py | tee -a $LOG_FILE
