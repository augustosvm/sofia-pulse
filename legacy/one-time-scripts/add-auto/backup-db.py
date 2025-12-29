#!/usr/bin/env python3
"""Backup do banco antes da normalização"""

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or 'localhost',
    'port': os.getenv('POSTGRES_PORT') or '5432',
    'user': os.getenv('POSTGRES_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or 'sofia_db',
}

def backup_stats():
    """Salva estatísticas do banco antes da normalização"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/stats_before_normalization_{timestamp}.txt'
    
    os.makedirs('backups', exist_ok=True)
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("BACKUP STATS - BEFORE NORMALIZATION\n")
        f.write(f"Data: {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        # Tabelas principais
        tables = [
            'sources', 'trends', 'organizations', 'persons', 'categories',
            'tech_trends', 'community_posts', 'patents',
            'countries', 'states', 'cities',
            'authors', 'institutions', 'companies'
        ]
        
        f.write("CONTAGEM DE REGISTROS:\n\n")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
                count = cur.fetchone()[0]
                f.write(f"{table:30s} {count:>15,} registros\n")
            except Exception as e:
                f.write(f"{table:30s} {'ERRO':>15s} ({str(e)[:50]})\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("TODAS AS TABELAS:\n\n")
        
        cur.execute("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_schema='sofia' AND table_name=t.table_name) as columns
            FROM information_schema.tables t
            WHERE table_schema = 'sofia'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        total_tables = 0
        for row in cur.fetchall():
            f.write(f"{row[0]:50s} {row[1]:>3d} colunas\n")
            total_tables += 1
        
        f.write(f"\nTotal: {total_tables} tabelas\n")
    
    conn.close()
    
    print(f"✅ Backup salvo: {backup_file}")
    return backup_file

if __name__ == '__main__':
    print("=" * 80)
    print("🔒 BACKUP DO BANCO - Antes da Normalização")
    print("=" * 80)
    print()
    
    backup_file = backup_stats()
    
    print()
    print("=" * 80)
    print("✅ BACKUP COMPLETO!")
    print("=" * 80)
    print()
    print(f"Arquivo: {backup_file}")
    print()
    print("Agora é seguro executar a normalização.")
    print()
