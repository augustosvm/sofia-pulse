#!/usr/bin/env python3
"""
Validate referential integrity across all normalized tables
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_orphaned_fks(cursor, table, fk_column, ref_table, ref_column='id'):
    """Check for orphaned foreign keys"""
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM sofia.{table} t
        WHERE t.{fk_column} IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM sofia.{ref_table} r
              WHERE r.{ref_column} = t.{fk_column}
          )
    """)
    count = cursor.fetchone()[0]
    return count

def check_unused_orgs(cursor):
    """Check for organizations not referenced anywhere"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM sofia.organizations o
        WHERE NOT EXISTS (
            SELECT 1 FROM sofia.funding_rounds WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.space_industry WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.jobs WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.market_data_brazil WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.market_data_nasdaq WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.global_universities_progress WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.world_ngos WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.hdx_humanitarian_data WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.hkex_ipos WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.startups WHERE organization_id = o.id
            UNION ALL
            SELECT 1 FROM sofia.nih_grants WHERE organization_id = o.id
        )
    """)
    return cursor.fetchone()[0]

def main():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

    cursor = conn.cursor()

    print("=" * 80)
    print("🔍 VALIDATING REFERENTIAL INTEGRITY")
    print("=" * 80)
    print()

    total_issues = 0

    # Check organization_id foreign keys
    print("📊 ORGANIZATION FOREIGN KEYS")
    print("-" * 80)

    org_tables = [
        'funding_rounds', 'space_industry', 'jobs', 'market_data_brazil',
        'market_data_nasdaq', 'global_universities_progress', 'world_ngos',
        'hdx_humanitarian_data', 'hkex_ipos', 'startups', 'nih_grants'
    ]

    for table in org_tables:
        orphaned = check_orphaned_fks(cursor, table, 'organization_id', 'organizations')
        status = "✅" if orphaned == 0 else "❌"
        print(f"{status} {table:.<40} {orphaned} orphaned FKs")
        total_issues += orphaned

    print()

    # Check country_id foreign keys
    print("🌍 COUNTRY FOREIGN KEYS")
    print("-" * 80)

    country_tables = [
        'jobs', 'tech_jobs', 'persons', 'authors', 'publications',
        'gdelt_events', 'cardboard_production', 'electricity_consumption',
        'energy_global', 'gender_names', 'startups', 'global_universities_progress',
        'world_ngos', 'funding_rounds', 'space_industry'
    ]

    for table in country_tables:
        try:
            orphaned = check_orphaned_fks(cursor, table, 'country_id', 'countries')
            status = "✅" if orphaned == 0 else "❌"
            print(f"{status} {table:.<40} {orphaned} orphaned FKs")
            total_issues += orphaned
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            print(f"⚠️  {table:.<40} No country_id column")

    print()

    # Check state_id foreign keys
    print("🏛️  STATE FOREIGN KEYS")
    print("-" * 80)

    state_tables = ['jobs', 'tech_jobs', 'comexstat_trade']

    for table in state_tables:
        try:
            orphaned = check_orphaned_fks(cursor, table, 'state_id', 'states')
            status = "✅" if orphaned == 0 else "❌"
            print(f"{status} {table:.<40} {orphaned} orphaned FKs")
            total_issues += orphaned
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            print(f"⚠️  {table:.<40} No state_id column")

    print()

    # Check city_id foreign keys
    print("🏙️  CITY FOREIGN KEYS")
    print("-" * 80)

    city_tables = ['jobs', 'tech_jobs']

    for table in city_tables:
        try:
            orphaned = check_orphaned_fks(cursor, table, 'city_id', 'cities')
            status = "✅" if orphaned == 0 else "❌"
            print(f"{status} {table:.<40} {orphaned} orphaned FKs")
            total_issues += orphaned
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            print(f"⚠️  {table:.<40} No city_id column")

    print()

    # Check unused organizations
    print("🏢 UNUSED ORGANIZATIONS")
    print("-" * 80)

    unused_orgs = check_unused_orgs(cursor)
    status = "✅" if unused_orgs == 0 else "⚠️ "
    print(f"{status} Organizations with no references: {unused_orgs}")

    print()
    print("=" * 80)

    if total_issues == 0 and unused_orgs == 0:
        print("✅ REFERENTIAL INTEGRITY: PERFECT")
    elif total_issues == 0:
        print(f"✅ REFERENTIAL INTEGRITY: OK ({unused_orgs} unused orgs)")
    else:
        print(f"❌ REFERENTIAL INTEGRITY: {total_issues} ISSUES FOUND")

    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
