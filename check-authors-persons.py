#!/usr/bin/env python3
"""Verifica se authors/persons já existem no banco"""

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

def check_table(conn, table_name):
    """Verifica se tabela existe e sua estrutura"""
    cur = conn.cursor()
    
    # Verificar se existe
    cur.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'sofia' 
            AND table_name = '{table_name}'
        )
    """)
    exists = cur.fetchone()[0]
    
    if not exists:
        print(f"❌ Tabela sofia.{table_name} NÃO EXISTE")
        return
    
    print(f"✅ Tabela sofia.{table_name} EXISTE")
    
    # Estrutura
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print(f"   Colunas ({len(cols)}):")
    for col in cols[:10]:
        print(f"      - {col[0]:30s} {col[1]}")
    if len(cols) > 10:
        print(f"      ... e mais {len(cols) - 10} colunas")
    
    # Contagem
    cur.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
    count = cur.fetchone()[0]
    print(f"   Registros: {count:,}")
    
    # Foreign keys que referenciam esta tabela
    cur.execute(f"""
        SELECT 
            tc.table_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND ccu.table_schema = 'sofia'
        AND ccu.table_name = '{table_name}'
    """)
    fks = cur.fetchall()
    if fks:
        print(f"   Referenciada por:")
        for fk in fks:
            print(f"      - {fk[0]}.{fk[1]}")
    
    print()

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    
    print("=" * 80)
    print("🔍 VERIFICANDO TABELAS EXISTENTES")
    print("=" * 80)
    print()
    
    # Verificar authors
    check_table(conn, 'authors')
    
    # Verificar persons
    check_table(conn, 'persons')
    
    # Verificar paper_authors
    check_table(conn, 'paper_authors')
    
    conn.close()

if __name__ == '__main__':
    main()
