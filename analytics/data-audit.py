#!/usr/bin/env python3
"""
Sofia Pulse - Data Audit
Verifica quais dados temos disponíveis para análise causal
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'sofia'),
    password=os.getenv('DB_PASSWORD', 'sofia123strong'),
    database=os.getenv('DB_NAME', 'sofia_db')
)

cur = conn.cursor()

print("=" * 80)
print("SOFIA PULSE - DATA AUDIT")
print("=" * 80)
print()

# Lista todas as tabelas com contagem de registros
cur.execute("""
    SELECT
        table_name,
        (xpath('/row/cnt/text()', query_to_xml(format('SELECT COUNT(*) as cnt FROM sofia.%I', table_name), false, true, '')))[1]::text::int as row_count
    FROM information_schema.tables
    WHERE table_schema = 'sofia' AND table_type = 'BASE TABLE'
    ORDER BY row_count DESC;
""")

print("📊 TABELAS DISPONÍVEIS:")
print()

total_records = 0
tables_data = []

for table, count in cur.fetchall():
    if count and count > 0:
        tables_data.append((table, count))
        total_records += count
        print(f"✅ {table:40s} {count:>10,} registros")

print()
print(f"TOTAL: {len(tables_data)} tabelas | {total_records:,} registros")
print()

# Verificar dados disponíveis para análises causais
print("=" * 80)
print("DADOS PARA ANÁLISES CAUSAIS:")
print("=" * 80)
print()

# 1. Papers (ArXiv + OpenAlex)
cur.execute("SELECT COUNT(*) FROM sofia.arxiv_ai_papers")
arxiv_count = cur.fetchone()[0]
print(f"📄 Papers ArXiv: {arxiv_count:,}")

cur.execute("SELECT COUNT(*) FROM sofia.openalex_papers")
openalex_count = cur.fetchone()[0]
print(f"📄 Papers OpenAlex: {openalex_count:,}")

# 2. Funding
cur.execute("SELECT COUNT(*), MIN(announced_date), MAX(announced_date) FROM sofia.funding_rounds")
funding = cur.fetchone()
print(f"💰 Funding Rounds: {funding[0]:,} ({funding[1]} a {funding[2]})")

# 3. GitHub
cur.execute("SELECT COUNT(*), COUNT(DISTINCT language) FROM sofia.github_trending")
github = cur.fetchone()
print(f"⭐ GitHub Repos: {github[0]:,} repos | {github[1]} linguagens")

# 4. CVEs
cur.execute("SELECT COUNT(*), MIN(published_date), MAX(published_date) FROM sofia.cybersecurity_events")
cves = cur.fetchone()
print(f"🔒 CVEs: {cves[0]:,} ({cves[1]} a {cves[2]})")

# 5. Space
cur.execute("SELECT COUNT(*) FROM sofia.space_industry")
space = cur.fetchone()[0]
print(f"🚀 Space Launches: {space:,}")

# 6. Socioeconomic
cur.execute("SELECT COUNT(*), COUNT(DISTINCT country_code) FROM sofia.socioeconomic_indicators")
socio = cur.fetchone()
print(f"🌍 Socioeconomic: {socio[0]:,} records | {socio[1]} países")

print()
print("=" * 80)
print("GAPS PARA ANÁLISES:")
print("=" * 80)
print()

# Verificar gaps temporais
cur.execute("""
    SELECT
        'arxiv_papers' as source,
        MIN(publication_date) as first_date,
        MAX(publication_date) as last_date,
        MAX(publication_date) - MIN(publication_date) as days_coverage
    FROM sofia.arxiv_ai_papers
    UNION ALL
    SELECT
        'funding',
        MIN(announced_date),
        MAX(announced_date),
        MAX(announced_date) - MIN(announced_date)
    FROM sofia.funding_rounds
""")

print("📅 Cobertura Temporal:")
for source, first, last, days in cur.fetchall():
    print(f"   {source:20s}: {first} → {last} ({days} dias)")

print()
print("✅ Audit completo!")

cur.close()
conn.close()
