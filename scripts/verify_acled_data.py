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
print("ACLED DATA VERIFICATION")
print("="*70)

# 1. Total ACLED
cur.execute("SELECT COUNT(*) FROM sofia.security_observations WHERE source='ACLED'")
print(f"\n1. Total ACLED observations: {cur.fetchone()[0]:,}")

# 2. Top countries
cur.execute("""
    SELECT country_code, country_name, COUNT(*) as cnt
    FROM sofia.security_observations
    WHERE source='ACLED' AND country_code IS NOT NULL
    GROUP BY country_code, country_name
    ORDER BY cnt DESC
    LIMIT 20
""")
print("\n2. Top 20 countries in ACLED:")
for code, name, cnt in cur.fetchall():
    print(f"   {code} - {name}: {cnt:,}")

# 3. LATAM check
cur.execute("""
    SELECT country_code, country_name, COUNT(*) as cnt
    FROM sofia.security_observations
    WHERE source='ACLED' 
      AND country_code IN ('BR','AR','CL','CO','PE','MX','VE','BO','EC','PY','UY')
    GROUP BY country_code, country_name
""")
latam = cur.fetchall()
print(f"\n3. LATAM in ACLED observations: {len(latam)} countries")
if latam:
    for code, name, cnt in latam:
        print(f"   {code} - {name}: {cnt:,}")
else:
    print("   NONE")

# 4. View check
cur.execute("SELECT COUNT(*) FROM sofia.mv_security_country_combined")
print(f"\n4. Countries in mv_security_country_combined: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT country_code, country_name
    FROM sofia.mv_security_country_combined
    WHERE country_code IN ('BR','AR','CL','CO','PE','MX')
""")
latam_view = cur.fetchall()
print(f"\n5. LATAM in view: {len(latam_view)} countries")
if latam_view:
    for code, name in latam_view:
        print(f"   {code} - {name}")
else:
    print("   NONE")

conn.close()
print("\n" + "="*70)
