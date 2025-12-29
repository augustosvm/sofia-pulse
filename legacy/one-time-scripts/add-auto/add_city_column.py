import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

# Adicionar coluna city
print("Adicionando coluna 'city' à tabela funding_rounds...")
cur.execute("ALTER TABLE sofia.funding_rounds ADD COLUMN IF NOT EXISTS city VARCHAR(255)")
conn.commit()
print("✅ Coluna 'city' adicionada!")

# Verificar
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='sofia' AND table_name='funding_rounds' ORDER BY ordinal_position")
print("\nColunas atualizadas:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

conn.close()
