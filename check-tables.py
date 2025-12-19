#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("TABELAS MASTER CRIADAS:")
for table in ['sources', 'types', 'trends', 'organizations', 'persons']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM sofia.{table}')
        print(f'{table}: {cur.fetchone()[0]:,}')
    except:
        print(f'{table}: NÃO EXISTE')

conn.close()
