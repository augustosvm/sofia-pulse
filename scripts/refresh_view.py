import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
conn.autocommit = True
cur = conn.cursor()

try:
    print("Refreshing materialized view...")
    cur.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_country_combined")
    print("✅ Success")
except Exception as e:
    print(f"❌ Error: {e}")

conn.close()
