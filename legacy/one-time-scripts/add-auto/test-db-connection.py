#!/usr/bin/env python3
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Conexão PostgreSQL OK")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   User: {DB_CONFIG['user']}")
    print(f"   DB: {DB_CONFIG['database']}")
    conn.close()
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
