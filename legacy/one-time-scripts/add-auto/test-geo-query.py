#!/usr/bin/env python3
"""Teste simples de query SQL com normalização geográfica"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or 'localhost',
    'port': os.getenv('POSTGRES_PORT') or '5432',
    'user': os.getenv('POSTGRES_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or 'sofia_db',
}

def test_query():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("Testando query com normalização geográfica...")
    print()
    
    query = """
    SELECT
        COALESCE(ci.name, fr.city, co.common_name, 'Unknown') as city,
        COALESCE(co.common_name, fr.country, 'Unknown') as country,
        COUNT(*) as deals_count
    FROM sofia.funding_rounds fr
    LEFT JOIN sofia.countries co ON fr.country_id = co.id
    LEFT JOIN sofia.cities ci ON fr.city_id = ci.id
    WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '365 days'
        AND (fr.country_id IS NOT NULL OR fr.country IS NOT NULL)
    GROUP BY ci.name, fr.city, co.common_name, fr.country
    LIMIT 5
    """
    
    try:
        cur.execute(query)
        results = cur.fetchall()
        
        print("✅ Query funcionou!")
        print()
        print("Resultados:")
        for row in results:
            print(f"  {row[0]}, {row[1]}: {row[2]} deals")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        print()
        print("Query:")
        print(query)
    
    conn.close()

if __name__ == '__main__':
    test_query()
