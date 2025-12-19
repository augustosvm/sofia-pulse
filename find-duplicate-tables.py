#!/usr/bin/env python3
"""
Script para identificar tabelas duplicadas no banco de dados
Procura por:
1. Tabelas com nomes similares
2. Tabelas com estruturas similares
3. Tabelas com dados duplicados
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or 'localhost',
    'port': os.getenv('POSTGRES_PORT') or '5432',
    'user': os.getenv('POSTGRES_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or 'sofia_db',
}

def get_all_tables(conn):
    """Lista todas as tabelas do schema sofia"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            table_name,
            (SELECT COUNT(*) FROM information_schema.columns 
             WHERE table_schema = 'sofia' AND table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'sofia'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    return cur.fetchall()

def get_table_structure(conn, table_name):
    """Retorna a estrutura de uma tabela"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    
    return cur.fetchall()

def get_table_row_count(conn, table_name):
    """Retorna o número de registros de uma tabela"""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
        return cur.fetchone()[0]
    except:
        return 0

def find_similar_table_names(tables):
    """Encontra tabelas com nomes similares"""
    similar = []
    table_names = [t['table_name'] for t in tables]
    
    for i, name1 in enumerate(table_names):
        for name2 in table_names[i+1:]:
            # Verificar se um nome contém o outro
            if name1 in name2 or name2 in name1:
                similar.append((name1, name2))
            # Verificar prefixos/sufixos comuns
            elif name1.replace('_', '') in name2.replace('_', '') or name2.replace('_', '') in name1.replace('_', ''):
                similar.append((name1, name2))
    
    return similar

def compare_table_structures(conn, table1, table2):
    """Compara a estrutura de duas tabelas"""
    struct1 = get_table_structure(conn, table1)
    struct2 = get_table_structure(conn, table2)
    
    cols1 = {c['column_name']: c['data_type'] for c in struct1}
    cols2 = {c['column_name']: c['data_type'] for c in struct2}
    
    common_cols = set(cols1.keys()) & set(cols2.keys())
    only_in_1 = set(cols1.keys()) - set(cols2.keys())
    only_in_2 = set(cols2.keys()) - set(cols1.keys())
    
    similarity = len(common_cols) / max(len(cols1), len(cols2)) if max(len(cols1), len(cols2)) > 0 else 0
    
    return {
        'similarity': similarity,
        'common_columns': len(common_cols),
        'total_columns_1': len(cols1),
        'total_columns_2': len(cols2),
        'only_in_1': list(only_in_1),
        'only_in_2': list(only_in_2),
        'common': list(common_cols)
    }

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    
    print("=" * 80)
    print("🔍 BUSCA POR TABELAS DUPLICADAS")
    print("=" * 80)
    print()
    
    # Listar todas as tabelas
    print("📊 Listando todas as tabelas...")
    tables = get_all_tables(conn)
    print(f"   Total: {len(tables)} tabelas")
    print()
    
    # Encontrar nomes similares
    print("=" * 80)
    print("🔎 TABELAS COM NOMES SIMILARES")
    print("=" * 80)
    print()
    
    similar_names = find_similar_table_names(tables)
    
    if similar_names:
        for table1, table2 in similar_names:
            count1 = get_table_row_count(conn, table1)
            count2 = get_table_row_count(conn, table2)
            
            print(f"📋 {table1} ({count1:,} registros)")
            print(f"📋 {table2} ({count2:,} registros)")
            
            # Comparar estruturas
            comparison = compare_table_structures(conn, table1, table2)
            print(f"   Similaridade: {comparison['similarity']:.1%}")
            print(f"   Colunas comuns: {comparison['common_columns']}")
            print(f"   Apenas em {table1}: {len(comparison['only_in_1'])}")
            print(f"   Apenas em {table2}: {len(comparison['only_in_2'])}")
            
            if comparison['similarity'] > 0.7:
                print("   ⚠️  POSSÍVEL DUPLICATA!")
            
            print()
    else:
        print("✅ Nenhuma tabela com nome similar encontrada")
    
    # Listar todas as tabelas com contagem
    print("=" * 80)
    print("📊 TODAS AS TABELAS (ordenadas por número de registros)")
    print("=" * 80)
    print()
    
    tables_with_counts = []
    for table in tables:
        count = get_table_row_count(conn, table['table_name'])
        tables_with_counts.append({
            'name': table['table_name'],
            'columns': table['column_count'],
            'rows': count
        })
    
    tables_with_counts.sort(key=lambda x: x['rows'], reverse=True)
    
    for t in tables_with_counts:
        print(f"  {t['name']:40s} {t['rows']:>12,} registros  ({t['columns']} colunas)")
    
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ Análise completa!")
    print("=" * 80)

if __name__ == '__main__':
    main()
