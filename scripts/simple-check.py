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
cur.execute("SELECT COUNT(*) FROM sofia.jobs")
print(f"TOTAL: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE DATE(collected_at) = CURRENT_DATE")
print(f"HOJE: {cur.fetchone()[0]}")
cur.execute("SELECT platform, COUNT(*) FROM sofia.jobs GROUP BY platform ORDER BY COUNT(*) DESC")
print("\nPOR PLATAFORMA:")
for p, cnt in cur.fetchall():
    print(f"  {p}: {cnt}")
c.close()
