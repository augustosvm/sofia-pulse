#!/usr/bin/env python3
"""Verifica tabelas de instituições existentes"""

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

def check_institutions(conn):
    """Verifica tabelas de instituições"""
    cur = conn.cursor()
    
    # Buscar tabelas com 'institution' no nome
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'sofia' 
        AND table_name LIKE '%institution%'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cur.fetchall()]
    
    print("=" * 80)
    print("🏛️  TABELAS DE INSTITUIÇÕES")
    print("=" * 80)
    print()
    
    for table in tables:
        # Estrutura
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
            AND table_name = '{table}'
            ORDER BY ordinal_position
        """)
        cols = cur.fetchall()
        
        # Contagem
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        
        print(f"📋 {table}")
        print(f"   Registros: {count:,}")
        print(f"   Colunas ({len(cols)}):")
        for col in cols[:8]:
            print(f"      - {col[0]:30s} {col[1]}")
        if len(cols) > 8:
            print(f"      ... e mais {len(cols) - 8} colunas")
        
        # Sample
        cur.execute(f"SELECT * FROM sofia.{table} LIMIT 3")
        samples = cur.fetchall()
        if samples:
            print(f"   Exemplos:")
            for sample in samples:
                print(f"      - {sample[1] if len(sample) > 1 else sample[0]}")
        
        print()

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    check_institutions(conn)
    conn.close()

if __name__ == '__main__':
    main()
