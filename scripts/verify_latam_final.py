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

print("="*70)
print("ACLED LATAM - Verificação Final")
print("="*70)

# 1. Total em security_observations
cur.execute("SELECT COUNT(*) FROM sofia.security_observations WHERE source='ACLED'")
print(f"\n1. Total ACLED observations: {cur.fetchone()[0]:,}")

# 2. LATAM em observations
cur.execute("""
    SELECT country_code, country_name, COUNT(*) as cnt
    FROM sofia.security_observations
    WHERE source='ACLED' 
      AND country_code IN ('BR','AR','CL','CO','PE','MX','VE','BO','EC','PY','UY')
    GROUP BY country_code, country_name
    ORDER BY cnt DESC
""")
latam_obs = cur.fetchall()
print(f"\n2. LATAM em observations: {len(latam_obs)} países")
for code, name, cnt in latam_obs:
    print(f"   {code} - {name}: {cnt:,}")

# 3. Total em mv_security_country_combined
cur.execute("SELECT COUNT(*) FROM sofia.mv_security_country_combined")
print(f"\n3. Total países na view: {cur.fetchone()[0]:,}")

# 4. LATAM na view
cur.execute("""
    SELECT country_code, country_name, total_risk
    FROM sofia.mv_security_country_combined
    WHERE country_code IN ('BR','AR','CL','CO','PE','MX','VE','BO','EC')
    ORDER BY total_risk DESC
""")
latam_view = cur.fetchall()
print(f"\n4. LATAM na view (API): {len(latam_view)} países")
for code, name, risk in latam_view:
    print(f"   {code} - {name}: risk={risk:.1f}")

conn.close()
print("\n" + "="*70)
