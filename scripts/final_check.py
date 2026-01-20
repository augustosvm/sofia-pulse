import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    dbname=os.getenv("POSTGRES_DB")
)
cur = conn.cursor()

print("DIAGNÓSTICO FINAL - View vs Observations")
print("="*70)

# 1. Países em observations
cur.execute("""
    SELECT DISTINCT country_code 
    FROM sofia.security_observations 
    WHERE source='ACLED' AND country_code IS NOT NULL
    ORDER BY country_code
""")
obs_countries = [r[0] for r in cur.fetchall()]
print(f"\n1. Países em observations: {len(obs_countries)}")

# 2. Países na view
cur.execute("SELECT country_code FROM sofia.mv_security_country_combined ORDER BY country_code")
view_countries = [r[0] for r in cur.fetchall()]
print(f"2. Países na view: {len(view_countries)}")

# 3. Diff
missing = set(obs_countries) - set(view_countries)
print(f"\n3. Países em observations MAS NÃO na view: {len(missing)}")
if missing:
    latam_missing = [c for c in missing if c in ['BR','AR','CL','CO','PE','MX','VE','BO','EC','HN','GT','HT']]
    print(f"   LATAM faltando: {sorted(latam_missing)}")
    print(f"   Todos faltando: {sorted(list(missing))[:30]}")

conn.close()
print("\n" + "="*70)
