#!/usr/bin/env python3
"""Add remaining columns to sofia.jobs"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB"),
)

cur = conn.cursor()

additional_columns = [
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS remote_type VARCHAR(20)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS city VARCHAR(255)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS seniority_level VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS employment_type VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS salary_min NUMERIC",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS salary_max NUMERIC",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(10)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS salary_period VARCHAR(20)",
]

print("Adicionando colunas restantes...")
for sql in additional_columns:
    try:
        cur.execute(sql)
        print(f"✅ {sql[40:80]}")
    except Exception as e:
        print(f"⚠️  {str(e)[:50]}")

conn.commit()
print("✅ Concluído!")
conn.close()
