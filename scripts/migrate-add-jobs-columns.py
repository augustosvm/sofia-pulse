#!/usr/bin/env python3
"""Migration: Add extra columns to sofia.jobs table"""
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

alterations = [
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS platform VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS company_size VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS experience_years_min INTEGER",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS experience_years_max INTEGER",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS visa_sponsorship BOOLEAN DEFAULT FALSE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS company_url TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS search_keyword VARCHAR(255)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR(50)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS skills TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS benefits TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS application_deadline DATE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP DEFAULT NOW()",
    "CREATE INDEX IF NOT EXISTS idx_jobs_platform ON sofia.jobs(platform)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_collected_at ON sofia.jobs(collected_at)",
]

print("=" * 70)
print("ADICIONANDO COLUNAS EXTRAS À TABELA sofia.jobs")
print("=" * 70)

for sql in alterations:
    try:
        cur.execute(sql)
        print(f"✅ {sql[:60]}...")
    except Exception as e:
        print(f"⚠️  {sql[:60]}... - {str(e)[:50]}")

conn.commit()
print("\n✅ Migration concluída com sucesso!")
print("=" * 70)

conn.close()
