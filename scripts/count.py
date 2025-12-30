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
cur.execute("SELECT COUNT(*), COUNT(DISTINCT platform), COUNT(DISTINCT company) FROM sofia.jobs")
total, plat, comp = cur.fetchone()
print(f"TOTAL: {total} vagas | {plat} plataformas | {comp} empresas")
c.close()
