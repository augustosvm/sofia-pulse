#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("ESTRUTURA DA TABELA PERSONS:")
print()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='persons' 
    ORDER BY ordinal_position
""")

for row in cur.fetchall():
    print(f"{row[0]:30s} {row[1]}")

print()
print("CAMPOS RELACIONADOS A GÊNERO:")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='persons'
    AND (column_name LIKE '%gender%' OR column_name LIKE '%sex%')
""")

gender_cols = cur.fetchall()
if gender_cols:
    for col in gender_cols:
        print(f"  - {col[0]}")
else:
    print("  ❌ NÃO TEM CAMPO DE GÊNERO/SEXO")

conn.close()
