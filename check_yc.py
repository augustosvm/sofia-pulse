import psycopg2
conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

# Verificar todas as tabelas
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'sofia' ORDER BY table_name")
print('Tabelas disponíveis:')
for r in cur.fetchall():
    print(f'  - {r[0]}')

# Verificar funding_rounds
cur.execute('SELECT COUNT(*) FROM sofia.funding_rounds')
print(f'\nfunding_rounds: {cur.fetchone()[0]} registros')

# Verificar se YC foi para outra tabela
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'sofia' AND table_name LIKE '%yc%' OR table_name LIKE '%combinator%'")
yc_tables = cur.fetchall()
if yc_tables:
    print('\nTabelas YC:')
    for r in yc_tables:
        print(f'  - {r[0]}')

conn.close()
