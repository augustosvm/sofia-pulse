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

print("🔍 Investigando relacionamentos entre tabelas")
print("=" * 80)
print()

# 1. Ver tabela dim_university
print("1. Estrutura de dim_university:")
cursor.execute("SELECT * FROM sofia.dim_university LIMIT 2")
print("Colunas:", [desc[0] for desc in cursor.description])
for row in cursor.fetchall():
    print(f"  Exemplo: {dict(zip([desc[0] for desc in cursor.description], row))}")
print()

# 2. Ver tabela global_universities_progress  
print("2. Estrutura de global_universities_progress:")
cursor.execute("SELECT * FROM sofia.global_universities_progress LIMIT 2")
print("Colunas:", [desc[0] for desc in cursor.description])
for row in cursor.fetchall():
    print(f"  Exemplo: {dict(zip([desc[0] for desc in cursor.description], row))}")
print()

# 3. Verificar se há foreign key entre person_papers e outras tabelas
print("3. Contagem de paper_source em person_papers:")
cursor.execute("""
    SELECT paper_source, COUNT(*) as count
    FROM sofia.person_papers
    GROUP BY paper_source
    ORDER BY count DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:,} papers")
print()

# 4. Ver se person tem informação de país/universidade
print("4. Verificando tabela person (se existir):")
try:
    cursor.execute("SELECT * FROM sofia.person LIMIT 2")
    print("Colunas:", [desc[0] for desc in cursor.description])
    for row in cursor.fetchall():
        print(f"  Exemplo: {dict(zip([desc[0] for desc in cursor.description], row))}")
except:
    print("  Tabela person não existe ou sem acesso")
print()

# 5. Ver distribuição de fields em person_papers
print("5. Top 20 fields/assuntos em person_papers:")
cursor.execute("""
    SELECT UNNEST(fields) as field, COUNT(*) as count
    FROM sofia.person_papers
    WHERE fields IS NOT NULL
    GROUP BY field
    ORDER BY count DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<50} {row[1]:>8,} papers")

cursor.close()
conn.close()
