#!/usr/bin/env python3
import psycopg2, os
from pathlib import Path

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip()

load_env()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)

cur = conn.cursor()

print("="*70)
print("FINAL MAP STATUS")
print("="*70)

cur.execute('SELECT COUNT(*) FROM sofia.mv_security_geo_points')
print(f'\nMap points: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(DISTINCT country_name) FROM sofia.mv_security_geo_points')
print(f'Countries: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM sofia.mv_security_geo_points WHERE country_name ILIKE '%ukraine%'")
ukraine = cur.fetchone()[0]
print(f'Ukraine points: {ukraine:,}')

if ukraine > 0:
    print("\nOK - Ukraine is on the map!")
else:
    print("\nWARNING - Ukraine not found")

print("\n" + "="*70)
print("The map should now show global hotspots.")
print("Refresh your browser to see the updated data.")
print("="*70)

cur.close()
conn.close()
