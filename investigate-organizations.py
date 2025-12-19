#!/usr/bin/env python3
"""3. Investiga por que organizations tem só 404 registros"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("3️⃣ INVESTIGANDO ORGANIZATIONS (404 de ~400k)")
print("=" * 80)
print()

# Verificar tabelas de origem
print("Tabelas de origem:")

cur.execute("SELECT COUNT(*) FROM sofia.brazil_research_institutions")
brazil = cur.fetchone()[0]
print(f"   brazil_research_institutions: {brazil:,}")

cur.execute("SELECT COUNT(*) FROM sofia.global_research_institutions")
global_inst = cur.fetchone()[0]
print(f"   global_research_institutions: {global_inst:,}")

print(f"\n   TOTAL ESPERADO: {brazil + global_inst:,}")

# Verificar institutions (pode ter sido renomeada)
try:
    cur.execute("SELECT COUNT(*) FROM sofia.institutions")
    institutions = cur.fetchone()[0]
    print(f"\n⚠️ ATENÇÃO: Tabela 'institutions' existe com {institutions:,} registros!")
    print("   Pode ser que os dados já estejam lá.")
except:
    print("\n   Tabela 'institutions' não existe.")

# Verificar organizations atual
cur.execute("SELECT COUNT(*) FROM sofia.organizations")
orgs = cur.fetchone()[0]
print(f"\nOrganizations atual: {orgs:,}")

# Verificar nomes duplicados
cur.execute("""
    SELECT COUNT(DISTINCT institution)
    FROM (
        SELECT institution FROM sofia.brazil_research_institutions
        UNION ALL
        SELECT institution FROM sofia.global_research_institutions
    ) sub
    WHERE institution IS NOT NULL
""")
unique_names = cur.fetchone()[0]
print(f"Nomes únicos nas tabelas origem: {unique_names:,}")

# Verificar se há constraint UNIQUE bloqueando
cur.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT LOWER(TRIM(institution)) as norm_name, COUNT(*) as cnt
        FROM (
            SELECT institution FROM sofia.brazil_research_institutions
            UNION ALL
            SELECT institution FROM sofia.global_research_institutions
        ) sub
        WHERE institution IS NOT NULL
        GROUP BY LOWER(TRIM(institution))
        HAVING COUNT(*) > 1
    ) dup
""")
duplicates = cur.fetchone()[0]
print(f"Nomes duplicados (normalized): {duplicates:,}")

print("\n" + "=" * 80)
print("DIAGNÓSTICO:")
if institutions > orgs:
    print(f"❌ PROBLEMA: Dados já estão em 'institutions' ({institutions:,} registros)")
    print("   SOLUÇÃO: Renomear institutions → organizations OU migrar dados")
else:
    print(f"❌ PROBLEMA: Migração incompleta")
    print(f"   Esperado: ~{unique_names:,}")
    print(f"   Atual: {orgs:,}")
    print(f"   Faltam: ~{unique_names - orgs:,}")
print("=" * 80)

conn.close()
