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
cur = conn.cursor()

try:
    view_def = cur.fetchone()[0]
    with open("view_def.sql", "w", encoding="utf-8") as f:
        f.write(view_def)
    print("Saved view_def.sql")
except Exception as e:
    print(f"Error: {e}")

conn.close()
