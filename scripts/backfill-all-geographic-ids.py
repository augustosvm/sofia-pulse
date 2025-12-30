#!/usr/bin/env python3
"""
Backfill Geographic IDs for All Normalized Tables
Populates country_id, state_id, city_id from existing text fields
"""

import os
import sys
from datetime import datetime

import psycopg2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.shared.geo_helpers import normalize_location

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '91.98.158.19'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db')
}


def backfill_jobs(conn):
    """Backfill jobs table (2.9k missing)"""
    print("\n1️⃣  JOBS TABLE")
    print("-" * 80)

    cur = conn.cursor()

    # Get jobs without country_id but with country text
    cur.execute(
        """
        SELECT id, country, city, location
        FROM sofia.jobs
        WHERE country_id IS NULL AND country IS NOT NULL
        LIMIT 5000
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} jobs sem country_id")

    updated = 0
    for job_id, country, city, location in rows:
        try:
            # Normalize location
            loc = normalize_location(conn, {"country": country, "city": city or location})

            if loc["country_id"]:
                cur.execute(
                    """
                    UPDATE sofia.jobs
                    SET country_id = %s, city_id = %s
                    WHERE id = %s
                """,
                    (loc["country_id"], loc["city_id"], job_id),
                )
                updated += 1

                if updated % 100 == 0:
                    conn.commit()
                    print(f"  Progresso: {updated}/{len(rows)}")
        except Exception as e:
            continue

    conn.commit()
    print(f"✅ Atualizados: {updated}/{len(rows)}")
    cur.close()


def backfill_persons(conn):
    """Backfill persons table (100k missing)"""
    print("\n2️⃣  PERSONS TABLE")
    print("-" * 80)

    cur = conn.cursor()

    # Get persons without country_id but with country text
    cur.execute(
        """
        SELECT id, country, city
        FROM sofia.persons
        WHERE country_id IS NULL AND country IS NOT NULL
        LIMIT 10000
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} persons sem country_id (limitado a 10k)")

    updated = 0
    for person_id, country, city in rows:
        try:
            loc = normalize_location(conn, {"country": country, "city": city})

            if loc["country_id"]:
                cur.execute(
                    """
                    UPDATE sofia.persons
                    SET country_id = %s, city_id = %s
                    WHERE id = %s
                """,
                    (loc["country_id"], loc["city_id"], person_id),
                )
                updated += 1

                if updated % 500 == 0:
                    conn.commit()
                    print(f"  Progresso: {updated}/{len(rows)}")
        except Exception as e:
            continue

    conn.commit()
    print(f"✅ Atualizados: {updated}/{len(rows)}")
    cur.close()


def backfill_socioeconomic(conn):
    """Backfill socioeconomic_indicators (21k missing)"""
    print("\n3️⃣  SOCIOECONOMIC_INDICATORS TABLE")
    print("-" * 80)

    cur = conn.cursor()

    # Get records without country_id but with country_name or country_code
    cur.execute(
        """
        SELECT id, country_name, country_code
        FROM sofia.socioeconomic_indicators
        WHERE country_id IS NULL
        AND (country_name IS NOT NULL OR country_code IS NOT NULL)
        LIMIT 25000
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} registros sem country_id")

    updated = 0
    for rec_id, country_name, country_code in rows:
        try:
            loc = normalize_location(conn, {"country": country_name or country_code})

            if loc["country_id"]:
                cur.execute(
                    """
                    UPDATE sofia.socioeconomic_indicators
                    SET country_id = %s
                    WHERE id = %s
                """,
                    (loc["country_id"], rec_id),
                )
                updated += 1

                if updated % 1000 == 0:
                    conn.commit()
                    print(f"  Progresso: {updated}/{len(rows)}")
        except Exception as e:
            continue

    conn.commit()
    print(f"✅ Atualizados: {updated}/{len(rows)}")
    cur.close()


def backfill_space_industry(conn):
    """Backfill space_industry (10% missing)"""
    print("\n4️⃣  SPACE_INDUSTRY TABLE")
    print("-" * 80)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, country
        FROM sofia.space_industry
        WHERE country_id IS NULL AND country IS NOT NULL
        LIMIT 1000
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} registros sem country_id")

    updated = 0
    for rec_id, country in rows:
        try:
            loc = normalize_location(conn, {"country": country})

            if loc["country_id"]:
                cur.execute(
                    """
                    UPDATE sofia.space_industry
                    SET country_id = %s
                    WHERE id = %s
                """,
                    (loc["country_id"], rec_id),
                )
                updated += 1
        except Exception as e:
            continue

    conn.commit()
    print(f"✅ Atualizados: {updated}/{len(rows)}")
    cur.close()


def add_missing_columns(conn):
    """Add country_id column to tables that don't have it"""
    print("\n5️⃣  ADDING MISSING COLUMNS")
    print("-" * 80)

    cur = conn.cursor()

    # brazil_security_data
    try:
        cur.execute(
            """
            ALTER TABLE sofia.brazil_security_data
            ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id),
            ADD COLUMN IF NOT EXISTS state_id INTEGER REFERENCES sofia.states(id),
            ADD COLUMN IF NOT EXISTS city_id INTEGER REFERENCES sofia.cities(id)
        """
        )
        conn.commit()
        print("✅ Adicionado country_id em brazil_security_data")
    except Exception as e:
        print(f"⚠️  brazil_security_data: {e}")

    cur.close()


def main():
    print("=" * 80)
    print("BACKFILL GEOGRAPHIC IDs - ALL TABLES")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao banco de dados")

        # Add missing columns first
        add_missing_columns(conn)

        # Backfill tables with missing data
        backfill_jobs(conn)
        backfill_persons(conn)
        backfill_socioeconomic(conn)
        backfill_space_industry(conn)

        conn.close()

        print()
        print("=" * 80)
        print("✅ BACKFILL CONCLUÍDO")
        print("=" * 80)
        print()
        print("PRÓXIMOS PASSOS:")
        print("1. Rodar collectors atualizados: women_brazil_data, sports_regional")
        print("2. Verificar cobertura novamente com: python3 /tmp/check_normalization_coverage.py")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
