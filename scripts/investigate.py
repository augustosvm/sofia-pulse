import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
c = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB"),
)
cur = c.cursor()

print("=" * 70)
print("🔍 INVESTIGANDO DISCREPÂNCIA NA CONTAGEM")
print("=" * 70)

# Total geral
cur.execute("SELECT COUNT(*) FROM sofia.jobs")
total = cur.fetchone()[0]
print(f"\n📊 Total de vagas no banco: {total}")

# Vagas coletadas hoje
cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE DATE(collected_at) = CURRENT_DATE")
today = cur.fetchone()[0]
print(f"📅 Coletadas hoje: {today}")

# Últimas 2 horas
cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE collected_at >= NOW() - INTERVAL '2 hours'")
recent = cur.fetchone()[0]
print(f"⏰ Últimas 2 horas: {recent}")

# Por plataforma
print(f"\n📱 Por plataforma:")
cur.execute("SELECT platform, COUNT(*) FROM sofia.jobs GROUP BY platform ORDER BY COUNT(*) DESC")
for platform, count in cur.fetchall():
    print(f"   {platform}: {count}")

# Datas
cur.execute("SELECT MIN(collected_at), MAX(collected_at) FROM sofia.jobs")
min_date, max_date = cur.fetchone()
print(f"\n📆 Primeira coleta: {min_date}")
print(f"📆 Última coleta: {max_date}")

# Verificar duplicatas por job_id
cur.execute("SELECT COUNT(*), COUNT(DISTINCT job_id) FROM sofia.jobs")
total_rows, unique_ids = cur.fetchone()
print(f"\n🔑 Total de linhas: {total_rows}")
print(f"🔑 job_ids únicos: {unique_ids}")
if total_rows != unique_ids:
    print(f"⚠️  ATENÇÃO: {total_rows - unique_ids} duplicatas encontradas!")

print("\n" + "=" * 70)
c.close()
