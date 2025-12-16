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

print("Estrutura da tabela persons:")
print("=" * 80)
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'sofia' AND table_name = 'persons'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<40} {row[1]}")

print()
print("Exemplo de dados em persons:")
print("=" * 80)
cursor.execute("SELECT * FROM sofia.persons LIMIT 3")
columns = [desc[0] for desc in cursor.description]
for row in cursor.fetchall():
    print(f"\nRegistro {row[0]}:")
    for i, col in enumerate(columns):
        if row[i]:
            print(f"  {col}: {str(row[i])[:100]}")

cursor.close()
conn.close()
