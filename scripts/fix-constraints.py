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

# Remover NOT NULL de TODAS as colunas que podem ter esse problema
columns_to_fix = ['sector', 'country', 'location', 'city', 'title', 'company', 'description', 'url']

for col in columns_to_fix:
    try:
        cur.execute(f'ALTER TABLE sofia.jobs ALTER COLUMN {col} DROP NOT NULL')
        print(f'✅ {col} - NOT NULL removido')
    except Exception as e:
        print(f'⚠️  {col} - {str(e)[:40]}')

c.commit()
print('\n✅ Constraints removidas!')
c.close()
