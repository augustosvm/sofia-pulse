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
conn.autocommit = True
cur = conn.cursor()

print("Recriando views sem filtro de 90 dias...")

# Read and modify SQL
with open('migrations/054_security_hybrid_views.sql', encoding='utf-8') as f:
    sql = f.read()

# Remove 90-day filter
sql = sql.replace(
    "AND event_time_start >= CURRENT_DATE - INTERVAL '90 days'",
    "-- REMOVED: AND event_time_start >= CURRENT_DATE - INTERVAL '90 days'"
)

# Execute
cur.execute(sql)

print("✅ Views recriadas com sucesso!")

# Verify
cur.execute("SELECT COUNT(*) FROM sofia.mv_security_country_combined")
total = cur.fetchone()[0]
print(f"Total países na view: {total}")

# Check LATAM
cur.execute("""
    SELECT country_code 
    FROM sofia.mv_security_country_combined 
    WHERE country_code IN ('BR','AR','CL','CO','PE','MX','VE','HN','GT')
    ORDER BY country_code
""")
latam = [r[0] for r in cur.fetchall()]
print(f"LATAM na view: {latam}")

conn.close()
