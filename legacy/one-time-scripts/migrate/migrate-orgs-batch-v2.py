#!/usr/bin/env python3
"""Migração em lote de organizations - VERSÃO CORRIGIDA"""

import psycopg2
import psycopg2.extras

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
# Remover autocommit para suportar named cursor
conn.autocommit = False 
cur = conn.cursor()

print("=" * 80)
print("📦 MIGRAÇÃO EM LOTE: ORGANIZATIONS (V2)")
print("=" * 80)
print()

# 1. Configurar
batch_size = 5000 # Reduzido para menos lock
total_migrated = 0

try:
    # Contar fonte
    cur.execute("SELECT COUNT(*) FROM sofia.global_research_institutions WHERE institution IS NOT NULL")
    total_source = cur.fetchone()[0]
    print(f"Total na fonte: {total_source:,}")
    conn.commit() # Commit para liberar

    # Contar destino antes
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    start_count = cur.fetchone()[0]
    print(f"Total atual em organizations: {start_count:,}")
    conn.commit() # Commit para liberar
    print()

    migrate_sql = """
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (normalized_name) DO NOTHING
    """
    
    # Criar cursor de leitura (named cursor requer transação)
    read_cur = conn.cursor(name='source_reader', cursor_factory=psycopg2.extras.DictCursor)
    read_cur.execute("""
        SELECT DISTINCT
            institution,
            'research_center' as type,
            jsonb_build_object('source', 'global_research_institutions', 'country', institution_country_name) as metadata
        FROM sofia.global_research_institutions
        WHERE institution IS NOT NULL
    """)
    
    # Cursor separado para escrita (sem nome)
    write_cur = conn.cursor()
    
    batch = []
    processed_count = 0
    
    while True:
        rows = read_cur.fetchmany(batch_size)
        if not rows:
            break
            
        processed_count += len(rows)
        
        # Preparar batch para inserção
        for row in rows:
            inst_name = row[0]
            inst_type = row[1]
            meta = row[2]
            
            # Sanitizar nome
            if not inst_name: continue
            
            # Inferir tipo melhor
            lower_name = inst_name.lower()
            if 'university' in lower_name or 'college' in lower_name:
                inst_type = 'university'
            elif 'hospital' in lower_name or 'clinic' in lower_name:
                inst_type = 'hospital'
            elif 'school' in lower_name:
                inst_type = 'school'
            
            norm_name = lower_name.strip()
            if not norm_name: continue
            
            batch.append((inst_name, norm_name, inst_type, psycopg2.extras.Json(meta)))
        
        # Inserir batch
        if batch:
            try:
                psycopg2.extras.execute_batch(write_cur, migrate_sql, batch)
                conn.commit() # Commit a cada lote
                total_migrated += len(batch)
                
                # Feedback a cada 50k
                if total_migrated % 50000 == 0 or total_migrated == len(batch):
                    print(f"   Migrados: {total_migrated:,} / {total_source:,} ({(total_migrated/total_source)*100:.1f}%)")
            except Exception as e:
                print(f"❌ Erro no batch: {e}")
                conn.rollback() # Rollback só do batch falho? Não, named cursor morreria.
                
                # Se der erro, aborta por segurança
                break
                
            batch = []

    print()
    print("✅ Migração concluída!")
    
    # Fechar named cursor
    read_cur.close()
    conn.commit()

except Exception as e:
    print(f"❌ Erro fatal: {e}")
    conn.rollback()

# 3. Validar
cur.execute("SELECT COUNT(*) FROM sofia.organizations")
final_count = cur.fetchone()[0]
print(f"Total FINAL em organizations: {final_count:,} (+{final_count - start_count:,})")

conn.close()
