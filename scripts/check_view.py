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

print("VERIFICAÇÃO FINAL - Por que API retorna 51 países?")
print("="*70)

# 1. Países na view
cur.execute("SELECT country_code FROM sofia.mv_security_country_combined ORDER BY country_code")
view_countries = [r[0] for r in cur.fetchall()]
print(f"\n1. Países na view: {len(view_countries)}")
print(f"   Sample: {view_countries[:20]}")

# 2. LATAM na view?
latam = ['BR','AR','CL','CO','PE','MX','VE','BO','EC','HN','GT','HT']
latam_in_view = [c for c in latam if c in view_countries]
latam_missing = [c for c in latam if c not in view_countries]

print(f"\n2. LATAM na view: {latam_in_view}")
print(f"   LATAM faltando: {latam_missing}")

# 3. Verificar se view tem filtro de structural_risk
cur.execute("""
    SELECT country_code, structural_risk 
    FROM sofia.mv_security_country_combined 
    WHERE country_code IN ('BR','AR','CL','CO','PE','MX')
    LIMIT 10
""")
latam_structural = cur.fetchall()
print(f"\n3. LATAM com structural_risk:")
for code, risk in latam_structural:
    print(f"   {code}: {risk}")

conn.close()
print("\n" + "="*70)
