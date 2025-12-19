#!/usr/bin/env python3
"""Migração em lote de organizations - VERSÃO SIMPLES (IN-MEMORY)"""

import psycopg2
import psycopg2.extras

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("📦 MIGRAÇÃO EM LOTE: ORGANIZATIONS (V3 - IN-MEMORY)")
print("=" * 80)
print()

try:
    # 1. Carregar TUDO na memória (400k rows não é grande pro servidor)
    print("1️⃣ Carregando dados da fonte...")
    cur.execute("""
        SELECT DISTINCT
            institution,
            'research_center' as type,
            jsonb_build_object('source', 'global_research_institutions', 'country', institution_country_name) as metadata
        FROM sofia.global_research_institutions
        WHERE institution IS NOT NULL
    """)
    rows = cur.fetchall()
    print(f"   Carregados {len(rows):,} registros na memória")
    
    # 2. Processar
    print("2️⃣ Processando e preparando batch...")
    batch = []
    
    for row in rows:
        inst_name = row[0]
        # inst_type = row[1] (vamos re-inferir)
        meta = row[2]
        
        if not inst_name: continue
        
        # Inferir tipo
        lower_name = inst_name.lower()
        if 'university' in lower_name or 'college' in lower_name:
            inst_type = 'university'
        elif 'hospital' in lower_name or 'clinic' in lower_name:
            inst_type = 'hospital'
        elif 'school' in lower_name:
            inst_type = 'school'
        else:
            inst_type = 'research_center'
        
        norm_name = lower_name.strip()
        if not norm_name: continue
        
        batch.append((inst_name, norm_name, inst_type, psycopg2.extras.Json(meta)))
    
    print(f"   Prontos para inserir: {len(batch):,} registros")
    
    # 3. Inserir
    print("3️⃣ Executando INSERT em lote...")
    
    migrate_sql = """
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (normalized_name) DO NOTHING
    """
    
    psycopg2.extras.execute_batch(cur, migrate_sql, batch, page_size=1000)
    print("   ✅ INSERT concluído")

    print()
    print("✅ Migração concluída com SUCESSO!")

except Exception as e:
    print(f"❌ Erro fatal: {e}")

# 4. Validar
cur.execute("SELECT COUNT(*) FROM sofia.organizations")
final_count = cur.fetchone()[0]
print(f"Total FINAL em organizations: {final_count:,}")

conn.close()
