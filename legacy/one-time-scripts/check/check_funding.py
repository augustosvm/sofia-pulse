import psycopg2
conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM sofia.funding_rounds')
total = cur.fetchone()[0]
print(f'Total funding rounds: {total}')
cur.execute('SELECT company_name, round_type FROM sofia.funding_rounds ORDER BY collected_at DESC LIMIT 10')
print('\nÚltimos 10:')
for r in cur.fetchall():
    print(f'  - {r[0]}: {r[1]}')
conn.close()
