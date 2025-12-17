import psycopg2
conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='sofia' AND table_name='funding_rounds' ORDER BY ordinal_position")
print('Colunas em sofia.funding_rounds:')
for col, dtype in cur.fetchall():
    print(f'  {col}: {dtype}')
conn.close()
