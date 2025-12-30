#!/usr/bin/env python3
"""
Backfill Organization IDs for Priority Tables
Migrates company names to normalized organizations table
"""

import os
import sys
from datetime import datetime

import psycopg2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.shared.org_helpers import get_or_create_organization

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '91.98.158.19'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db')
}


def backfill_funding_rounds(conn):
    """Backfill funding_rounds.organization_id from company_name"""
    print("\n1️⃣  FUNDING_ROUNDS")
    print("-" * 80)

    cur = conn.cursor()

    # Get funding rounds without organization_id
    cur.execute(
        """
        SELECT id, company_name, country, city
        FROM sofia.funding_rounds
        WHERE organization_id IS NULL
        AND company_name IS NOT NULL
        AND company_name != ''
        ORDER BY id
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} funding rounds sem organization_id")

    updated = 0

    for funding_id, company_name, country, city in rows:
        try:
            # Get or create organization using correct signature
            location = f"{city}, {country}" if city and country else (city or country)

            org_id = get_or_create_organization(
                cur,  # cursor, not conn
                company_name,  # company_name (positional)
                None,  # company_url
                location,  # location
                country,  # country
                "funding_rounds",  # source
            )

            if org_id:
                # Update funding_round with organization_id
                cur.execute(
                    """
                    UPDATE sofia.funding_rounds
                    SET organization_id = %s
                    WHERE id = %s
                """,
                    (org_id, funding_id),
                )

                updated += 1

                if updated % 100 == 0:
                    conn.commit()
                    print(f"  Progresso: {updated}/{len(rows)}")

        except Exception as e:
            print(f"  ⚠️  Erro em '{company_name}': {str(e)[:60]}")
            continue

    conn.commit()

    # Stats
    cur.execute(
        """
        SELECT COUNT(DISTINCT organization_id)
        FROM sofia.funding_rounds
        WHERE organization_id IS NOT NULL
    """
    )
    unique_orgs = cur.fetchone()[0]

    print(f"✅ Atualizados: {updated}/{len(rows)}")
    print(f"📊 Organizações únicas: {unique_orgs}")
    cur.close()


def backfill_space_industry(conn):
    """Backfill space_industry.organization_id from company"""
    print("\n2️⃣  SPACE_INDUSTRY")
    print("-" * 80)

    cur = conn.cursor()

    # Get space industry records without organization_id
    cur.execute(
        """
        SELECT id, company, country
        FROM sofia.space_industry
        WHERE organization_id IS NULL
        AND company IS NOT NULL
        AND company != ''
        ORDER BY id
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} registros sem organization_id")

    updated = 0

    for space_id, company, country in rows:
        try:
            # Get or create organization using correct signature
            org_id = get_or_create_organization(
                cur,  # cursor
                company,  # company_name
                None,  # company_url
                None,  # location
                country,  # country
                "space_industry",  # source
            )

            if org_id:
                cur.execute(
                    """
                    UPDATE sofia.space_industry
                    SET organization_id = %s
                    WHERE id = %s
                """,
                    (org_id, space_id),
                )

                updated += 1

                if updated % 200 == 0:
                    conn.commit()
                    print(f"  Progresso: {updated}/{len(rows)}")

        except Exception as e:
            print(f"  ⚠️  Erro em '{company}': {str(e)[:60]}")
            continue

    conn.commit()

    # Stats
    cur.execute(
        """
        SELECT COUNT(DISTINCT organization_id)
        FROM sofia.space_industry
        WHERE organization_id IS NOT NULL
    """
    )
    unique_orgs = cur.fetchone()[0]

    print(f"✅ Atualizados: {updated}/{len(rows)}")
    print(f"📊 Organizações únicas: {unique_orgs}")
    cur.close()


def backfill_tech_jobs(conn):
    """Backfill tech_jobs.organization_id from company"""
    print("\n3️⃣  TECH_JOBS")
    print("-" * 80)

    cur = conn.cursor()

    # Get tech jobs without organization_id
    cur.execute(
        """
        SELECT id, company, company_url
        FROM sofia.tech_jobs
        WHERE organization_id IS NULL
        AND company IS NOT NULL
        AND company != ''
        ORDER BY id
    """
    )

    rows = cur.fetchall()
    print(f"Encontrados {len(rows)} jobs sem organization_id")

    updated = 0

    for job_id, company, company_url in rows:
        try:
            # Get or create organization using correct signature
            org_id = get_or_create_organization(
                cur,  # cursor
                company,  # company_name
                company_url,  # company_url
                None,  # location
                None,  # country
                "tech_jobs",  # source
            )

            if org_id:
                cur.execute(
                    """
                    UPDATE sofia.tech_jobs
                    SET organization_id = %s
                    WHERE id = %s
                """,
                    (org_id, job_id),
                )

                updated += 1

                if updated % 100 == 0:
                    conn.commit()
                    print(f"  Progresso: {updated}/{len(rows)}")

        except Exception as e:
            print(f"  ⚠️  Erro em '{company}': {str(e)[:60]}")
            continue

    conn.commit()

    # Stats
    cur.execute(
        """
        SELECT COUNT(DISTINCT organization_id)
        FROM sofia.tech_jobs
        WHERE organization_id IS NOT NULL
    """
    )
    unique_orgs = cur.fetchone()[0]

    print(f"✅ Atualizados: {updated}/{len(rows)}")
    print(f"📊 Organizações únicas: {unique_orgs}")
    cur.close()


def show_coverage_stats(conn):
    """Show final coverage statistics"""
    print("\n" + "=" * 80)
    print("COVERAGE FINAL")
    print("=" * 80)
    print()

    cur = conn.cursor()

    tables = [("funding_rounds", "company_name"), ("space_industry", "company"), ("tech_jobs", "company")]

    for table, company_col in tables:
        cur.execute(
            f"""
            SELECT
                COUNT(*) as total,
                COUNT(organization_id) as with_org_id,
                COUNT({company_col}) as with_company,
                ROUND(100.0 * COUNT(organization_id) / NULLIF(COUNT({company_col}), 0), 1) as pct
            FROM sofia.{table}
        """
        )
        total, with_org, with_company, pct = cur.fetchone()

        status = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "❌"
        print(f"{status} {table:20} {with_org:>6}/{with_company:<6} = {pct:>5}%")

    # Total unique organizations created
    cur.execute(
        """
        SELECT COUNT(DISTINCT id)
        FROM sofia.organizations
        WHERE metadata->>'source' IN ('funding_rounds', 'space_industry', 'tech_jobs')
    """
    )
    new_orgs = cur.fetchone()[0]

    print()
    print(f"📊 Total de organizações únicas criadas/linkadas: {new_orgs}")

    cur.close()


def main():
    print("=" * 80)
    print("BACKFILL ORGANIZATION IDs - PRIORITY TABLES")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao banco de dados")

        # Run migration first
        print("\n📝 Executando migration 042...")
        cur = conn.cursor()
        with open("migrations/042_add_organization_id_to_priority_tables.sql", "r") as f:
            migration_sql = f.read()
            cur.execute(migration_sql)
            conn.commit()
        cur.close()
        print("✅ Migration 042 executada")

        # Backfill data
        backfill_funding_rounds(conn)
        backfill_space_industry(conn)
        backfill_tech_jobs(conn)

        # Show stats
        show_coverage_stats(conn)

        conn.close()

        print()
        print("=" * 80)
        print("✅ BACKFILL CONCLUÍDO")
        print("=" * 80)
        print()
        print("BENEFÍCIOS:")
        print("• Funding rounds linkados a organizações → correlação com jobs")
        print("• Space industry normalizado → tracking de empresas espaciais")
        print("• Tech jobs linkados → deduplicação de empresas")
        print()
        print("QUERIES DE EXEMPLO:")
        print("-- Empresas com funding E jobs:")
        print("SELECT o.name, COUNT(DISTINCT f.id) as funding_rounds, COUNT(DISTINCT j.id) as jobs")
        print("FROM sofia.organizations o")
        print("LEFT JOIN sofia.funding_rounds f ON f.organization_id = o.id")
        print("LEFT JOIN sofia.jobs j ON j.organization_id = o.id")
        print("GROUP BY o.id, o.name")
        print("HAVING COUNT(DISTINCT f.id) > 0 AND COUNT(DISTINCT j.id) > 0")
        print("ORDER BY funding_rounds DESC;")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
