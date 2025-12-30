#!/usr/bin/env python3
"""
Verificar estrutura das tabelas para normalização geográfica
"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER", "sofia"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB", "sofia_db"),
)

cur = conn.cursor()

tables_to_check = ["nih_grants", "acled_conflicts", "funding_rounds", "tech_jobs", "arxiv_papers"]

for table in tables_to_check:
    print(f"\n{'='*60}")
    print(f"Tabela: {table}")
    print("=" * 60)

    # Verificar se tabela existe
    cur.execute(
        f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'sofia' AND table_name = '{table}'
        )
    """
    )

    if not cur.fetchone()[0]:
        print(f"❌ Tabela não existe")
        continue

    # Buscar colunas geográficas
    cur.execute(
        f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = '{table}'
        AND (column_name LIKE '%country%' 
             OR column_name LIKE '%city%' 
             OR column_name LIKE '%state%' 
             OR column_name LIKE '%location%'
             OR column_name LIKE '%admin%')
        ORDER BY column_name
    """
    )

    columns = cur.fetchall()
    if columns:
        print("Colunas geográficas encontradas:")
        for col_name, col_type in columns:
            print(f"  - {col_name} ({col_type})")
    else:
        print("Nenhuma coluna geográfica encontrada")

    # Contar registros
    cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
    count = cur.fetchone()[0]
    print(f"\nTotal de registros: {count:,}")

cur.close()
conn.close()
