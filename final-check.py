#!/usr/bin/env python3
import psycopg2
c=psycopg2.connect(host='localhost',user='sofia',password='sofia123strong',database='sofia_db')
cur=c.cursor()

print("RESULTADO FINAL DA NORMALIZAÇÃO:")
print()

cur.execute('SELECT t.name, COUNT(*) FROM sofia.person_roles pr JOIN sofia.types t ON pr.role_id=t.id GROUP BY t.name ORDER BY COUNT(*) DESC')
print("PERSON_ROLES:")
for r in cur.fetchall():
    print(f'  {r[0]:20s} {r[1]:,}')

cur.execute('SELECT COUNT(*) FROM sofia.trends')
print(f'\nTRENDS: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(*) FROM sofia.organizations')
print(f'ORGANIZATIONS: {cur.fetchone()[0]:,}')

c.close()
