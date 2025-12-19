#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("RESULTADO DA NORMALIZAÇÃO:")
print()

tables = ['sources', 'types', 'trends', 'organizations', 'persons', 'person_roles']

for table in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM sofia.{table}')
        count = cur.fetchone()[0]
        print(f'{table:20s} {count:>10,}')
    except Exception as e:
        print(f'{table:20s} ERRO')

print()
print("DISTRIBUIÇÃO:")

# Types por categoria
try:
    cur.execute("SELECT category, COUNT(*) FROM sofia.types GROUP BY category ORDER BY category")
    print("\nTypes por categoria:")
    for row in cur.fetchall():
        print(f'  {row[0]:30s} {row[1]:>5}')
except:
    pass

# Organizations por tipo
try:
    cur.execute("SELECT type, COUNT(*) FROM sofia.organizations GROUP BY type ORDER BY COUNT(*) DESC LIMIT 5")
    print("\nOrganizations por tipo (top 5):")
    for row in cur.fetchall():
        print(f'  {row[0]:30s} {row[1]:>10,}')
except:
    pass

# Person roles
try:
    cur.execute("""
        SELECT t.name, COUNT(*) 
        FROM sofia.person_roles pr
        JOIN sofia.types t ON pr.role_id = t.id
        GROUP BY t.name
        ORDER BY COUNT(*) DESC
    """)
    print("\nPerson roles:")
    for row in cur.fetchall():
        print(f'  {row[0]:30s} {row[1]:>10,}')
except:
    pass

conn.close()
