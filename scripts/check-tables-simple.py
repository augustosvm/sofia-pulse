import psycopg2
import os
from pathlib import Path

env = Path(".env")
for line in open(env, encoding='utf-8'):
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
cur = conn.cursor()

print("="*60)
print("SECURITY HYBRID MODEL - STATUS DAS TABELAS")
print("="*60)

tables = {
    "security_observations": "Tabela Canonica",
    "security_events": "ACLED Source",
    "gdelt_events": "GDELT Source",
    "mv_security_country_combined": "View Hybrid (API)",
    "mv_security_country_acled": "View ACLED",
    "mv_security_country_gdelt": "View GDELT",
}

for table, desc in tables.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        print(f"{desc:30} {count:>10,}")
    except:
        print(f"{desc:30} {'NAO EXISTE':>10}")

print("\n" + "="*60)
print("SOURCES NA TABELA CANONICA")
print("="*60)

try:
    cur.execute("SELECT source, COUNT(*) FROM sofia.security_observations GROUP BY source ORDER BY COUNT(*) DESC")
    for source, count in cur.fetchall():
        print(f"{source:30} {count:>10,}")
except:
    print("Tabela vazia ou nao existe")

conn.close()
