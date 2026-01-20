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

print("--- ACLED Stats in security_observations ---")
cur.execute("SELECT COUNT(*), COUNT(country_code) FROM sofia.security_observations WHERE source = 'ACLED'")
total, present = cur.fetchone()
print(f"Total ACLED rows: {total}")
print(f"Rows with country_code: {present}")

if present > 0:
    print("\nSample country codes:")
    cur.execute("SELECT DISTINCT country_code, country_name FROM sofia.security_observations WHERE source='ACLED' LIMIT 20")
    for row in cur.fetchall():
        print(row)
else:
    print("\nChecking why country_code is NULL...")
    cur.execute("SELECT DISTINCT country_name FROM sofia.security_observations WHERE source='ACLED' LIMIT 10")
    print("Country names in observations:")
    for row in cur.fetchall():
        print(row)

    print("\nChecking matching in dim_country...")
    cur.execute("SELECT country_name_en, country_code_iso2 FROM sofia.dim_country LIMIT 10")
    print("Reference dim_country:")
    for row in cur.fetchall():
        print(row)

conn.close()
