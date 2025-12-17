#!/usr/bin/env python3
"""Complete migration - add ALL missing columns"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)

cur = conn.cursor()

# TODAS as colunas que podem estar faltando
all_columns = [
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS skills_required TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS job_id VARCHAR(255)",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS tags TEXT[]",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS requirements TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS responsibilities TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS nice_to_have TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS apply_url TEXT",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS views_count INTEGER DEFAULT 0",
    "ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS applicants_count INTEGER DEFAULT 0",
    # Criar índice único em job_id se não existir
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_job_id ON sofia.jobs(job_id)",
]

print("=" * 70)
print("ADICIONANDO TODAS AS COLUNAS NECESSÁRIAS")
print("=" * 70)

for sql in all_columns:
    try:
        cur.execute(sql)
        print(f"✅ {sql[:65]}...")
    except Exception as e:
        print(f"⚠️  {sql[:65]}... - {str(e)[:40]}")

conn.commit()
print("\n✅ Schema completo!")
print("=" * 70)

conn.close()
