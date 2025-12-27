#!/usr/bin/env python3
"""
Fast Backfill Organization IDs - Optimized Version
Processes in small batches with frequent commits
"""

import os
import sys
import psycopg2
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.shared.org_helpers import get_or_create_organization

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '91.98.158.19'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('DB_NAME', 'sofia_db')
}

BATCH_SIZE = 50  # Process 50 records at a time
COMMIT_FREQUENCY = 25  # Commit every 25 records


def backfill_table(conn, table_name, company_col, extra_cols=None):
    """Generic backfill function for any table"""
    print(f"\n📊 {table_name.upper()}")
    print("-" * 80)

    cur = conn.cursor()

    # Count total to process
    cur.execute(f"""
        SELECT COUNT(*)
        FROM sofia.{table_name}
        WHERE organization_id IS NULL
        AND {company_col} IS NOT NULL
        AND {company_col} != ''
    """)
    total = cur.fetchone()[0]

    if total == 0:
        print("   ✅ Nada para processar")
        cur.close()
        return

    print(f"   Encontrados {total:,} registros sem organization_id")

    # Build SELECT query
    select_cols = ['id', company_col]
    if extra_cols:
        select_cols.extend(extra_cols)

    offset = 0
    updated = 0
    errors = 0

    while offset < total:
        # Get batch
        cur.execute(f"""
            SELECT {', '.join(select_cols)}
            FROM sofia.{table_name}
            WHERE organization_id IS NULL
            AND {company_col} IS NOT NULL
            AND {company_col} != ''
            ORDER BY id
            LIMIT {BATCH_SIZE} OFFSET {offset}
        """)

        batch = cur.fetchall()

        for row in batch:
            record_id = row[0]
            company_name = row[1]

            # Extract extra fields
            company_url = None
            location = None
            country = None

            if extra_cols:
                if 'company_url' in extra_cols:
                    idx = select_cols.index('company_url')
                    company_url = row[idx] if idx < len(row) else None

                if 'country' in extra_cols:
                    idx = select_cols.index('country')
                    country = row[idx] if idx < len(row) else None

                if 'city' in extra_cols:
                    idx = select_cols.index('city')
                    city = row[idx] if idx < len(row) else None
                    if city and country:
                        location = f"{city}, {country}"
                    elif city:
                        location = city

            try:
                # Get or create organization
                org_id = get_or_create_organization(
                    cur,
                    company_name,
                    company_url,
                    location,
                    country,
                    table_name
                )

                if org_id:
                    cur.execute(f"""
                        UPDATE sofia.{table_name}
                        SET organization_id = %s
                        WHERE id = %s
                    """, (org_id, record_id))
                    updated += 1

                    # Commit frequently
                    if updated % COMMIT_FREQUENCY == 0:
                        conn.commit()

            except Exception as e:
                errors += 1
                if errors < 5:  # Only show first few errors
                    print(f"   ⚠️  '{company_name}': {str(e)[:50]}")

        offset += BATCH_SIZE

        # Progress update
        progress = min(offset, total)
        pct = (progress / total) * 100
        print(f"   Progresso: {progress:,}/{total:,} ({pct:.1f}%) | Atualizados: {updated:,}", end='\r')

    # Final commit
    conn.commit()

    # Stats
    cur.execute(f"""
        SELECT COUNT(DISTINCT organization_id)
        FROM sofia.{table_name}
        WHERE organization_id IS NOT NULL
    """)
    unique_orgs = cur.fetchone()[0]

    print()  # New line after progress
    print(f"   ✅ Concluído: {updated:,}/{total:,} atualizados")
    print(f"   📊 Organizações únicas: {unique_orgs:,}")
    if errors > 0:
        print(f"   ⚠️  Erros: {errors}")

    cur.close()


def main():
    print("=" * 80)
    print("BACKFILL ORGANIZATIONS - FAST MODE")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Batch size: {BATCH_SIZE} | Commit frequency: {COMMIT_FREQUENCY}")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao banco de dados")

        # Run migration first
        print("\n📝 Executando migration 042...")
        cur = conn.cursor()
        try:
            with open('migrations/042_add_organization_id_to_priority_tables.sql', 'r') as f:
                migration_sql = f.read()
                cur.execute(migration_sql)
                conn.commit()
            print("✅ Migration 042 executada")
        except Exception as e:
            print(f"⚠️  Migration: {str(e)[:60]}")
            conn.rollback()
        cur.close()

        # Backfill tables
        backfill_table(conn, 'funding_rounds', 'company_name', ['country', 'city'])
        backfill_table(conn, 'space_industry', 'company', ['country'])
        backfill_table(conn, 'tech_jobs', 'company', ['company_url'])

        # Final stats
        print("\n" + "=" * 80)
        print("COVERAGE FINAL")
        print("=" * 80)

        cur = conn.cursor()

        for table in ['funding_rounds', 'space_industry', 'tech_jobs']:
            cur.execute(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(organization_id) as with_org
                FROM sofia.{table}
            """)
            total, with_org = cur.fetchone()
            pct = (with_org / total * 100) if total else 0
            status = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "❌"
            print(f"{status} {table:25} {with_org:>6}/{total:<6} = {pct:>5.1f}%")

        # Total organizations
        cur.execute("SELECT COUNT(*) FROM sofia.organizations")
        total_orgs = cur.fetchone()[0]
        print(f"\n📊 Total organizações: {total_orgs:,}")

        cur.close()
        conn.close()

        print("\n" + "=" * 80)
        print("✅ BACKFILL CONCLUÍDO")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
