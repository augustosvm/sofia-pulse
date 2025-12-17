#!/usr/bin/env python3
import psycopg2

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

print("Estrutura completa de person_papers:")
print("=" * 80)
cursor.execute("SELECT * FROM sofia.person_papers LIMIT 3")
print("Colunas:", [desc[0] for desc in cursor.description])
print()
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"Registro {i}:")
    for j, col in enumerate(cursor.description):
        print(f"  {col[0]}: {row[j]}")
    print()

cursor.close()
conn.close()
