#!/usr/bin/env python3
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
c.autocommit = False
cur = c.cursor()

try:
    # Rollback any pending transaction
    c.rollback()

    # Set default for posted_date and source
    cur.execute("ALTER TABLE sofia.jobs ALTER COLUMN posted_date SET DEFAULT NOW()")
    cur.execute("ALTER TABLE sofia.jobs ALTER COLUMN source SET DEFAULT 'unknown'")
    c.commit()
    print("✅ Defaults definidos")

    # Now drop NOT NULL
    cur.execute("ALTER TABLE sofia.jobs ALTER COLUMN posted_date DROP NOT NULL")
    cur.execute("ALTER TABLE sofia.jobs ALTER COLUMN source DROP NOT NULL")
    c.commit()
    print("✅ NOT NULL removido")

except Exception as e:
    c.rollback()
    print(f"❌ Erro: {e}")

c.close()
