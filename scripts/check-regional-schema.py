#!/usr/bin/env python3
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', '91.98.158.19'),
    port=int(os.getenv('POSTGRES_PORT', 5432)),
    user=os.getenv('POSTGRES_USER', 'dbs_sofia'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB', 'sofia')
)

cursor = conn.cursor()

cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_schema = 'acled_aggregated'
      AND table_name = 'regional'
    ORDER BY ordinal_position
""")

print("Schema of acled_aggregated.regional:")
print(f"{'Column':<30} {'Type':<20} {'Max Length':<12}")
print("-" * 65)

for row in cursor.fetchall():
    col_name, data_type, max_len = row
    max_len_str = str(max_len) if max_len else '-'
    print(f"{col_name:<30} {data_type:<20} {max_len_str:<12}")

cursor.close()
conn.close()
