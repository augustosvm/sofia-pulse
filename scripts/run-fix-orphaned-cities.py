#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

with open('migrations/050_fix_orphaned_city_ids.sql', 'r') as f:
    sql = f.read()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
conn.set_session(autocommit=True)
cursor = conn.cursor()

print("🚀 Fixing orphaned city_id...")
cursor.execute(sql)

for notice in conn.notices:
    print(notice.strip())

cursor.close()
conn.close()
print("✅ Done!")
