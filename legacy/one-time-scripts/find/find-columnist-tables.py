#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("PROCURANDO TABELAS DE COLUNISTAS/WORDPRESS:")
print()

# Buscar tabelas com 'columnist', 'wordpress', 'wp', 'author', 'writer'
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia'
    AND (
        table_name LIKE '%columnist%' 
        OR table_name LIKE '%wordpress%'
        OR table_name LIKE '%wp_%'
        OR table_name LIKE '%writer%'
        OR table_name LIKE '%blog%'
        OR table_name LIKE '%post%'
        OR table_name LIKE '%article%'
    )
    ORDER BY table_name
""")

tables = cur.fetchall()

if tables:
    for table in tables:
        table_name = table[0]
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
        count = cur.fetchone()[0]
        
        # Mostrar estrutura
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema='sofia' AND table_name='{table_name}'
            ORDER BY ordinal_position
            LIMIT 10
        """)
        cols = [r[0] for r in cur.fetchall()]
        
        print(f"📋 {table_name}")
        print(f"   Registros: {count:,}")
        print(f"   Colunas: {', '.join(cols[:5])}...")
        print()
else:
    print("❌ Nenhuma tabela encontrada")

conn.close()
