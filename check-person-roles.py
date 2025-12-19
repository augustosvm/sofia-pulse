#!/usr/bin/env python3
"""1. Verifica resultado da correção de person_roles"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("1️⃣ VERIFICANDO PERSON_ROLES")
print("=" * 80)
print()

# Distribuição por role
cur.execute("""
    SELECT t.name, COUNT(*) as count
    FROM sofia.person_roles pr
    JOIN sofia.types t ON pr.role_id = t.id
    GROUP BY t.name
    ORDER BY count DESC
""")

print("Distribuição de roles:")
total = 0
for row in cur.fetchall():
    print(f"   {row[0]:20s} {row[1]:>10,}")
    total += row[1]

print(f"\n   {'TOTAL':20s} {total:>10,}")

# Pessoas com múltiplos roles
cur.execute("""
    SELECT COUNT(DISTINCT person_id) as pessoas_com_multiplos_roles
    FROM (
        SELECT person_id, COUNT(*) as role_count
        FROM sofia.person_roles
        GROUP BY person_id
        HAVING COUNT(*) > 1
    ) sub
""")

multi = cur.fetchone()[0]
print(f"\nPessoas com múltiplos roles: {multi:,}")

# Verificar se inventors e developers foram adicionados
cur.execute("""
    SELECT 
        COUNT(CASE WHEN t.normalized_name = 'researcher' THEN 1 END) as researchers,
        COUNT(CASE WHEN t.normalized_name = 'inventor' THEN 1 END) as inventors,
        COUNT(CASE WHEN t.normalized_name = 'developer' THEN 1 END) as developers
    FROM sofia.person_roles pr
    JOIN sofia.types t ON pr.role_id = t.id
""")

row = cur.fetchone()
print(f"\nBreakdown:")
print(f"   Researchers: {row[0]:,}")
print(f"   Inventors:   {row[1]:,}")
print(f"   Developers:  {row[2]:,}")

if row[1] > 0 and row[2] > 0:
    print("\n✅ CORREÇÃO BEM-SUCEDIDA! Inventors e Developers foram adicionados.")
else:
    print("\n❌ CORREÇÃO FALHOU! Ainda faltam Inventors ou Developers.")

conn.close()
