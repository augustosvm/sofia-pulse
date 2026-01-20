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

print("DIAGNÓSTICO RÁPIDO")
print("="*50)

# 1. Observations
cur.execute("SELECT COUNT(*) FROM sofia.security_observations WHERE source='ACLED'")
obs_total = cur.fetchone()[0]
print(f"1. ACLED observations: {obs_total:,}")

# 2. LATAM em observations
cur.execute("""
    SELECT country_code, COUNT(*) 
    FROM sofia.security_observations 
    WHERE source='ACLED' AND country_code IN ('BR','AR','CL','CO','PE','MX')
    GROUP BY country_code
""")
latam_obs = cur.fetchall()
print(f"2. LATAM em observations: {len(latam_obs)} países")
for code, cnt in latam_obs:
    print(f"   {code}: {cnt:,}")

# 3. View
cur.execute("SELECT COUNT(*) FROM sofia.mv_security_country_combined")
view_total = cur.fetchone()[0]
print(f"\n3. Países na view: {view_total:,}")

# 4. LATAM na view
cur.execute("""
    SELECT country_code 
    FROM sofia.mv_security_country_combined 
    WHERE country_code IN ('BR','AR','CL','CO','PE','MX')
""")
latam_view = [r[0] for r in cur.fetchall()]
print(f"4. LATAM na view: {latam_view if latam_view else 'NENHUM'}")

# 5. Sample da view
cur.execute("SELECT country_code FROM sofia.mv_security_country_combined LIMIT 10")
sample = [r[0] for r in cur.fetchall()]
print(f"5. Sample view: {sample}")

conn.close()
print("="*50)
