#!/usr/bin/env python3
"""
ACLED Regional → Security Events ETL
Importa dados de acled_aggregated.regional para sofia.security_events
"""
import psycopg2
from psycopg2.extras import execute_values
import os
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB")
}

def main():
    print("="*70)
    print("ACLED Regional → Security Events ETL")
    print("="*70)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Limpa dados ACLED regionais antigos de security_events
    print("\n🧹 Limpando dados regionais antigos...")
    cur.execute("""
        DELETE FROM sofia.security_events 
        WHERE source = 'ACLED_AGGREGATED'
          AND source_id LIKE 'aggregated-latin-america%'
    """)
    print(f"   Removidos {cur.rowcount:,} registros antigos")
    
    # Busca dados de acled_aggregated.regional
    print("\n📥 Buscando dados de acled_aggregated.regional...")
    cur.execute("""
        SELECT 
            dataset_slug,
            region,
            country,
            admin1,
            admin2,
            year,
            month,
            week,
            centroid_latitude,
            centroid_longitude,
            events,
            fatalities,
            event_type,
            disorder_type,
            metadata,
            source_file_hash
        FROM acled_aggregated.regional
        WHERE dataset_slug = 'aggregated-latin-america-caribbean'
          AND events IS NOT NULL
          AND centroid_latitude IS NOT NULL
          AND centroid_longitude IS NOT NULL
        ORDER BY year DESC, month DESC, week DESC
    """)
    
    rows = cur.fetchall()
    print(f"   Encontrados {len(rows):,} registros")
    
    if len(rows) == 0:
        print("❌ Nenhum dado encontrado em acled_aggregated.regional")
        return
    
    # Transforma para security_events
    print("\n🔄 Transformando dados...")
    records = []
    for row in rows:
        (dataset_slug, region, country, admin1, admin2, year, month, week,
         lat, lon, events, fatalities, event_type, disorder_type, metadata, file_hash) = row
        
        # Cria source_id único
        unique_str = f"{dataset_slug}_{country}_{admin1}_{admin2}_{year}_{month}_{week}_{event_type}"
        source_id = hashlib.md5(unique_str.encode()).hexdigest()[:16]
        
        # Monta event_date (primeiro dia da semana)
        if year and week:
            # Aproximação: primeira segunda-feira do ano + (week-1) * 7 dias
            from datetime import date, timedelta
            jan1 = date(year, 1, 1)
            # Encontra a primeira segunda-feira
            days_to_monday = (7 - jan1.weekday()) % 7
            first_monday = jan1 + timedelta(days=days_to_monday)
            event_date = first_monday + timedelta(weeks=week-1)
        else:
            event_date = None
        
        # Monta raw_payload
        raw_payload = {
            "region": region,
            "admin1": admin1,
            "admin2": admin2,
            "event_type": event_type,
            "disorder_type": disorder_type,
            "week": week,
            **(metadata if metadata else {})
        }
        
        records.append((
            'ACLED_AGGREGATED',
            source_id,
            country,
            admin1 or '',
            admin2 or '',
            float(lat),
            float(lon),
            event_date,
            int(events) if events else 0,
            int(fatalities) if fatalities else 0,
            raw_payload
        ))
    
    # Insere em security_events
    print(f"\n💾 Inserindo {len(records):,} registros em sofia.security_events...")
    execute_values(cur, """
        INSERT INTO sofia.security_events (
            source, source_id, country_name, admin1, city,
            latitude, longitude, event_date, event_count, fatalities, raw_payload
        ) VALUES %s
        ON CONFLICT (source, source_id) DO UPDATE SET
            event_count = EXCLUDED.event_count,
            fatalities = EXCLUDED.fatalities,
            raw_payload = EXCLUDED.raw_payload
    """, records)
    
    print(f"   ✅ {len(records):,} registros inseridos/atualizados")
    
    # Verifica
    cur.execute("""
        SELECT COUNT(*) FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
    """)
    total = cur.fetchone()[0]
    print(f"\n📊 Total em security_events (ACLED_AGGREGATED): {total:,}")
    
    # Amostra
    cur.execute("""
        SELECT country_name, COUNT(*) as cnt
        FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
        GROUP BY country_name
        ORDER BY cnt DESC
        LIMIT 10
    """)
    print("\n🌎 Top 10 países:")
    for country, cnt in cur.fetchall():
        print(f"   {country}: {cnt:,}")
    
    conn.close()
    print("\n" + "="*70)
    print("✅ ETL CONCLUÍDO")
    print("="*70)

if __name__ == "__main__":
    main()
