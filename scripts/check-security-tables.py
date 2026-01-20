#!/usr/bin/env python3
"""
Check all Security Hybrid Model tables
"""
import psycopg2
import os
from pathlib import Path

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip()

load_env()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
cur = conn.cursor()

print("="*70)
print("SECURITY HYBRID MODEL - TABELAS E DADOS")
print("="*70)

tables = [
    ("sofia.security_observations", "Tabela Canônica"),
    ("sofia.security_events", "ACLED Source"),
    ("sofia.gdelt_events", "GDELT Source"),
    ("sofia.world_bank_data", "World Bank Source"),
    ("sofia.brazil_security_data", "Brasil Crime"),
    ("sofia.brazil_women_violence", "Brasil Violência Mulher"),
    ("sofia.mv_security_country_acled", "View ACLED"),
    ("sofia.mv_security_country_gdelt", "View GDELT"),
    ("sofia.mv_security_country_structural", "View Structural"),
    ("sofia.mv_security_country_combined", "View Hybrid (API)"),
]

for table, desc in tables:
    schema, name = table.split('.')
    
    # Check if exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        )
    """, (schema, name))
    
    exists = cur.fetchone()[0]
    
    if exists:
        # Get count
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {desc:30} {table:45} {count:,} registros")
        except Exception as e:
            print(f"❌ {desc:30} {table:45} ERRO: {e}")
    else:
        print(f"❌ {desc:30} {table:45} NÃO EXISTE")

print("\n" + "="*70)
print("DIAGNÓSTICO")
print("="*70)

# Check canonical table
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema='sofia' AND table_name='security_observations')")
if cur.fetchone()[0]:
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT source) FROM sofia.security_observations")
    total, sources = cur.fetchone()
    print(f"\nTabela Canônica: {total:,} registros, {sources} sources")
    
    if total > 0:
        cur.execute("SELECT source, COUNT(*) FROM sofia.security_observations GROUP BY source")
        print("\nPor source:")
        for source, count in cur.fetchall():
            print(f"  {source:20} {count:,}")
    else:
        print("\n⚠️ Tabela canônica VAZIA - precisa executar normalizers!")
else:
    print("\n❌ Tabela canônica NÃO EXISTE - precisa executar migration 053!")

# Check views
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema='sofia' AND table_name='mv_security_country_combined')")
if cur.fetchone()[0]:
    cur.execute("SELECT COUNT(*) FROM sofia.mv_security_country_combined")
    count = cur.fetchone()[0]
    if count == 0:
        print("\n⚠️ View hybrid VAZIA - precisa refresh!")
        print("   Execute: SELECT sofia.refresh_security_hybrid_views();")
else:
    print("\n❌ View hybrid NÃO EXISTE - precisa executar migration 054!")

cur.close()
conn.close()

print("\n" + "="*70)
