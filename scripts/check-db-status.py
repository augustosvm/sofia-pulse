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

# Total
cur.execute('SELECT COUNT(*) FROM sofia.jobs')
total = cur.fetchone()[0]
print(f'📊 Total vagas no banco: {total}')

# Colunas
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='jobs' 
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print(f'\n✅ Tabela tem {len(cols)} colunas')
print('\nColunas principais:')
for col in cols[:15]:
    print(f'  - {col}')
if len(cols) > 15:
    print(f'  ... e mais {len(cols)-15} colunas')

c.close()
