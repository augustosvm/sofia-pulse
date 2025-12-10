#!/usr/bin/env python3
import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
c = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = c.cursor()

# Pegar TODAS as colunas da tabela
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='jobs' AND is_nullable='NO'
""")

columns_with_not_null = [r[0] for r in cur.fetchall()]

print(f"Removendo NOT NULL de {len(columns_with_not_null)} colunas...")

for col in columns_with_not_null:
    try:
        cur.execute(f'ALTER TABLE sofia.jobs ALTER COLUMN {col} DROP NOT NULL')
        print(f'✅ {col}')
    except Exception as e:
        print(f'⚠️  {col} - {str(e)[:30]}')

c.commit()
print(f'\n✅ {len(columns_with_not_null)} constraints removidas!')
c.close()
