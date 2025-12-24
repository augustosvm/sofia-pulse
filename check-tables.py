#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("VERIFICANDO TABELAS:")
for table in ['sources', 'types', 'trends', 'organizations', 'persons']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM sofia.{table}')
        count = cur.fetchone()[0]
        print(f'{table}: {count}')
    except Exception as e:
        print(f'{table}: ERRO - {str(e)[:80]}')

conn.close()
