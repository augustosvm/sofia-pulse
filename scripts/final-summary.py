#!/usr/bin/env python3
import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
c = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = c.cursor()

print("=" * 70)
print("📊 RESUMO FINAL DA COLETA DE VAGAS")
print("=" * 70)

# Total
cur.execute('SELECT COUNT(*), COUNT(DISTINCT platform), COUNT(DISTINCT company) FROM sofia.jobs')
total, platforms, companies = cur.fetchone()
print(f"\n✅ Total: {total} vagas")
print(f"✅ Plataformas: {platforms}")
print(f"✅ Empresas: {companies}")

# Por plataforma
print("\n📱 Por plataforma:")
cur.execute('SELECT platform, COUNT(*) FROM sofia.jobs GROUP BY platform ORDER BY COUNT(*) DESC LIMIT 10')
for platform, count in cur.fetchall():
    print(f"   {platform}: {count} vagas")

# Últimas coletadas
print("\n🆕 Últimas 5 vagas coletadas:")
cur.execute('SELECT title, company, platform, collected_at FROM sofia.jobs ORDER BY collected_at DESC LIMIT 5')
for title, company, platform, collected in cur.fetchall():
    print(f"   - {title[:40]} @ {company} ({platform})")

print("\n" + "=" * 70)
c.close()
