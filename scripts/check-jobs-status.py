#!/usr/bin/env python3
"""Verificar status das coletas de vagas"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

cur = conn.cursor()

print("=" * 70)
print("STATUS DAS COLETAS DE VAGAS")
print("=" * 70)

# Total e datas
cur.execute("SELECT COUNT(*), MAX(collected_at), MIN(collected_at) FROM sofia.jobs")
total, last, first = cur.fetchone()
print(f"\n📊 RESUMO GERAL:")
print(f"   Total de vagas: {total}")
print(f"   Primeira coleta: {first}")
print(f"   Última coleta: {last}")

if last:
    days_ago = (datetime.now() - last.replace(tzinfo=None)).days
    print(f"   ⏰ Última coleta foi há {days_ago} dias")

# Por plataforma
print(f"\n📱 POR PLATAFORMA:")
cur.execute("""
    SELECT platform, COUNT(*), MAX(collected_at), MIN(collected_at)
    FROM sofia.jobs 
    GROUP BY platform 
    ORDER BY MAX(collected_at) DESC NULLS LAST
""")

for platform, count, last_col, first_col in cur.fetchall():
    if last_col:
        days = (datetime.now() - last_col.replace(tzinfo=None)).days
        status = "🟢" if days < 7 else ("🟡" if days < 30 else "🔴")
        print(f"   {status} {platform}: {count} vagas (última: {last_col.strftime('%Y-%m-%d')} - há {days} dias)")
    else:
        print(f"   ⚪ {platform}: {count} vagas (sem data de coleta)")

# Vagas recentes (últimos 30 dias)
print(f"\n📅 VAGAS DOS ÚLTIMOS 30 DIAS:")
cur.execute("""
    SELECT platform, COUNT(*) 
    FROM sofia.jobs 
    WHERE collected_at >= NOW() - INTERVAL '30 days'
    GROUP BY platform
    ORDER BY COUNT(*) DESC
""")
recent = cur.fetchall()
if recent:
    for platform, count in recent:
        print(f"   - {platform}: {count} vagas")
else:
    print("   ❌ NENHUMA vaga coletada nos últimos 30 dias!")

conn.close()
print("=" * 70)
