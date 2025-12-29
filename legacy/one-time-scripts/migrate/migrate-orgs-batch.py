#!/usr/bin/env python3
"""Migração em lote de organizations"""

import psycopg2
import time

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("📦 MIGRAÇÃO EM LOTE: ORGANIZATIONS")
print("=" * 80)
print()

# 1. Configurar
batch_size = 10000
total_migrated = 0

# Contar fonte
cur.execute("SELECT COUNT(*) FROM sofia.global_research_institutions WHERE institution IS NOT NULL")
total_source = cur.fetchone()[0]
print(f"Total na fonte: {total_source:,}")

# Contar destino antes
cur.execute("SELECT COUNT(*) FROM sofia.organizations")
start_count = cur.fetchone()[0]
print(f"Total atual em organizations: {start_count:,}")
print()

try:
    # 2. Loop de migração
    # Usando LIMIT e OFFSET é lento em tabelas grandes, melhor usar cursor server-side ou ID ranges
    # Aqui vamos usar cursor server-side via named cursor
    
    migrate_sql = """
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (normalized_name) DO NOTHING
    """
    
    # Criar cursor de leitura para a fonte
    read_cur = conn.cursor(name='source_reader')
    read_cur.execute("""
        SELECT DISTINCT
            institution,
            'research_center' as type,
            jsonb_build_object('source', 'global_research_institutions', 'country', institution_country_name)
        FROM sofia.global_research_institutions
        WHERE institution IS NOT NULL
    """)
    
    batch = []
    while True:
        rows = read_cur.fetchmany(batch_size)
        if not rows:
            break
            
        # Preparar batch para inserção
        for row in rows:
            inst_name = row[0]
            inst_type = row[1]
            meta = row[2]
            
            # Inferir tipo melhor
            lower_name = inst_name.lower()
            if 'university' in lower_name or 'college' in lower_name:
                inst_type = 'university'
            elif 'hospital' in lower_name or 'clinic' in lower_name:
                inst_type = 'hospital'
            elif 'school' in lower_name:
                inst_type = 'school'
            
            # Sanitizar nome
            norm_name = lower_name.strip()
            if not norm_name: continue
            
            batch.append((inst_name, norm_name, inst_type, meta))
        
        # Inserir batch
        if batch:
            psycopg2.extras.execute_batch(cur, migrate_sql, batch)
            total_migrated += len(batch)
            print(f"   Migrados: {total_migrated:,} / {total_source:,} ({(total_migrated/total_source)*100:.1f}%)")
            batch = []

    print()
    print("✅ Migração concluída!")

except Exception as e:
    print(f"❌ Erro: {e}")

# 3. Validar
cur.execute("SELECT COUNT(*) FROM sofia.organizations")
final_count = cur.fetchone()[0]
print(f"Total FINAL em organizations: {final_count:,} (+{final_count - start_count:,})")

conn.close()
