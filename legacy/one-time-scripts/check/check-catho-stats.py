#!/usr/bin/env python3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

cur = conn.cursor()

# Total de vagas do Catho
cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE platform = 'catho'")
total = cur.fetchone()[0]

# Vagas únicas
cur.execute("SELECT COUNT(DISTINCT job_id) FROM sofia.jobs WHERE platform = 'catho'")
unicos = cur.fetchone()[0]

# Coletadas hoje
cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE platform = 'catho' AND collected_at::date = CURRENT_DATE")
hoje = cur.fetchone()[0]

print("=" * 50)
print("📊 ESTATÍSTICAS CATHO")
print("=" * 50)
print(f"Total de vagas: {total}")
print(f"Vagas únicas (job_id): {unicos}")
print(f"Coletadas hoje: {hoje}")
print("=" * 50)

conn.close()
