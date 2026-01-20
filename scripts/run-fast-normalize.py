#!/usr/bin/env python3
import os, psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', '91.98.158.19'),
    port=5432,
    user=os.getenv('POSTGRES_USER', 'dbs_sofia'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB', 'sofia')
)

with open('scripts/fast-normalize-acled.sql', 'r') as f:
    sql = f.read()

cursor = conn.cursor()
for statement in sql.split(';'):
    if statement.strip() and not statement.strip().startswith('--'):
        print(f"Executing: {statement.strip()[:80]}...")
        cursor.execute(statement)
        conn.commit()
        if cursor.description:
            result = cursor.fetchall()
            for row in result:
                print(f"  Result: {row}")

cursor.close()
conn.close()
print("\n✅ Done!")
