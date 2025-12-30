#!/usr/bin/env python3
"""Add ALL possible missing columns at once"""
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

# TODAS as colunas possíveis que podem estar faltando
all_possible_columns = [
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS sector VARCHAR(100)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_health_insurance BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_dental_insurance BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_vision_insurance BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_401k BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_pto BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_remote_option BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_equity BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS source_url TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS logo_url TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS company_description TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS team_size VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS funding_stage VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS tech_stack TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS languages TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS certifications TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS education_level VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS work_authorization VARCHAR(100)",
]

print("Adicionando TODAS as colunas possíveis...")
for sql in all_possible_columns:
    try:
        cur.execute(sql)
        col_name = sql.split("EXISTS ")[1].split(" ")[0]
        print(f"✅ {col_name}")
    except Exception as e:
        print(f"⚠️  {str(e)[:50]}")

c.commit()
print("\n✅ Schema completo!")
c.close()
