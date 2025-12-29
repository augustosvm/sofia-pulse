#!/usr/bin/env python3
"""Verificar estrutura das tabelas countries e cities"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or 'localhost',
    'port': os.getenv('POSTGRES_PORT') or '5432',
    'user': os.getenv('POSTGRES_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or 'sofia_db',
}

def check_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("Verificando estrutura das tabelas...")
    print()
    
    # Verificar colunas de countries
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = 'countries'
        ORDER BY ordinal_position
    """)
    
    print("📊 Tabela sofia.countries:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    print()
    
    # Verificar colunas de cities
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = 'cities'
        ORDER BY ordinal_position
    """)
    
    print("📊 Tabela sofia.cities:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    print()
    
    # Sample data
    cur.execute("SELECT * FROM sofia.countries LIMIT 3")
    print("📝 Sample countries:")
    for row in cur.fetchall():
        print(f"  {row}")
    
    print()
    
    cur.execute("SELECT * FROM sofia.cities LIMIT 3")
    print("📝 Sample cities:")
    for row in cur.fetchall():
        print(f"  {row}")
    
    conn.close()

if __name__ == '__main__':
    check_tables()
