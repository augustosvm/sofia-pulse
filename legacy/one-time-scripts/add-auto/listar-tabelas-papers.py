#!/usr/bin/env python3
import psycopg2

# Ler senha do .env
password = 'your_password_here'
try:
    with open('/home/ubuntu/sofia-pulse/.env', 'r') as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                password = line.split('=', 1)[1].strip()
                break
except:
    pass

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# Listar todas as tabelas
cursor.execute("""
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname IN ('public', 'sofia')
AND tablename LIKE '%paper%' OR tablename LIKE '%universit%' OR tablename LIKE '%research%'
ORDER BY tablename
""")

print("Tabelas relacionadas a papers/universidades/pesquisa:")
print("=" * 80)
for row in cursor.fetchall():
    print(f"{row[0]}.{row[1]}")

cursor.close()
conn.close()
