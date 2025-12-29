#!/usr/bin/env python3
"""
Audit normalization coverage across all tables
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_coverage(cursor, table, id_column, name_column=None):
    """Get normalization coverage percentage"""
    # Total records
    cursor.execute(f"SELECT COUNT(*) FROM sofia.{table}")
    total = cursor.fetchone()[0]

    if total == 0:
        return 0, 0, 0, 0

    # Normalized (has ID)
    cursor.execute(f"SELECT COUNT(*) FROM sofia.{table} WHERE {id_column} IS NOT NULL")
    normalized = cursor.fetchone()[0]

    # Has name but no ID (could be normalized)
    if name_column:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM sofia.{table}
            WHERE {id_column} IS NULL
              AND {name_column} IS NOT NULL
              AND {name_column} != ''
        """)
        unnormalized = cursor.fetchone()[0]
    else:
        unnormalized = total - normalized

    # NULL name (legitimate NULL)
    if name_column:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM sofia.{table}
            WHERE {name_column} IS NULL OR {name_column} = ''
        """)
        null_name = cursor.fetchone()[0]
    else:
        null_name = 0

    coverage = (normalized / total * 100) if total > 0 else 0

    return total, normalized, unnormalized, coverage

def main():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

    cursor = conn.cursor()

    print("=" * 100)
    print("📊 NORMALIZATION COVERAGE AUDIT")
    print("=" * 100)
    print()

    # Organization coverage
    print("🏢 ORGANIZATION NORMALIZATION")
    print("-" * 100)
    print(f"{'Table':<40} {'Total':>10} {'Normalized':>12} {'Missing':>10} {'Coverage':>10}")
    print("-" * 100)

    org_tables = [
        ('funding_rounds', 'organization_id', 'company_name'),
        ('space_industry', 'organization_id', 'company'),
        ('jobs', 'organization_id', 'company'),
        ('market_data_brazil', 'organization_id', 'company'),
        ('market_data_nasdaq', 'organization_id', 'company'),
        ('global_universities_progress', 'organization_id', 'institution_name'),
        ('world_ngos', 'organization_id', 'name'),
        ('hdx_humanitarian_data', 'organization_id', 'organization'),
        ('hkex_ipos', 'organization_id', 'company'),
        ('startups', 'organization_id', 'name'),
        ('nih_grants', 'organization_id', 'organization'),
    ]

    org_total = 0
    org_normalized = 0

    for table, id_col, name_col in org_tables:
        try:
            total, normalized, unnormalized, coverage = get_coverage(cursor, table, id_col, name_col)
            status = "✅" if coverage >= 95 else "⚠️ " if coverage >= 80 else "❌"
            print(f"{status} {table:<37} {total:>10,} {normalized:>12,} {unnormalized:>10,} {coverage:>9.1f}%")
            org_total += total
            org_normalized += normalized
        except Exception as e:
            print(f"❌ {table:<37} Error: {e}")
            conn.rollback()

    org_coverage = (org_normalized / org_total * 100) if org_total > 0 else 0
    print("-" * 100)
    print(f"{'TOTAL':<40} {org_total:>10,} {org_normalized:>12,} {org_total-org_normalized:>10,} {org_coverage:>9.1f}%")
    print()

    # Country coverage
    print("🌍 COUNTRY NORMALIZATION")
    print("-" * 100)
    print(f"{'Table':<40} {'Total':>10} {'Normalized':>12} {'Missing':>10} {'Coverage':>10}")
    print("-" * 100)

    country_tables = [
        ('jobs', 'country_id', 'country'),
        ('tech_jobs', 'country_id', 'country'),
        ('persons', 'country_id', 'country'),
        ('authors', 'country_id', 'primary_country'),
        ('publications', 'country_id', 'institution_country'),
        ('gdelt_events', 'country_id', 'action_geo_country'),
        ('cardboard_production', 'country_id', 'country'),
        ('electricity_consumption', 'country_id', 'country'),
        ('energy_global', 'country_id', 'country'),
        ('gender_names', 'country_id', 'country_code'),
        ('startups', 'country_id', 'country'),
        ('global_universities_progress', 'country_id', 'country_code'),
        ('world_ngos', 'country_id', 'headquarters_country'),
        ('funding_rounds', 'country_id', 'country'),
        ('space_industry', 'country_id', 'country'),
        ('comexstat_trade', 'country_id', 'country_name'),
    ]

    country_total = 0
    country_normalized = 0

    for table, id_col, name_col in country_tables:
        try:
            total, normalized, unnormalized, coverage = get_coverage(cursor, table, id_col, name_col)
            status = "✅" if coverage >= 95 else "⚠️ " if coverage >= 80 else "❌"
            print(f"{status} {table:<37} {total:>10,} {normalized:>12,} {unnormalized:>10,} {coverage:>9.1f}%")
            country_total += total
            country_normalized += normalized
        except Exception as e:
            print(f"❌ {table:<37} Error: {e}")
            conn.rollback()

    country_coverage = (country_normalized / country_total * 100) if country_total > 0 else 0
    print("-" * 100)
    print(f"{'TOTAL':<40} {country_total:>10,} {country_normalized:>12,} {country_total-country_normalized:>10,} {country_coverage:>9.1f}%")
    print()

    # State coverage
    print("🏛️  STATE NORMALIZATION")
    print("-" * 100)
    print(f"{'Table':<40} {'Total':>10} {'Normalized':>12} {'Missing':>10} {'Coverage':>10}")
    print("-" * 100)

    state_tables = [
        ('jobs', 'state_id', 'state'),
        ('comexstat_trade', 'state_id', 'state_code'),
    ]

    state_total = 0
    state_normalized = 0

    for table, id_col, name_col in state_tables:
        try:
            total, normalized, unnormalized, coverage = get_coverage(cursor, table, id_col, name_col)
            status = "✅" if coverage >= 95 else "⚠️ " if coverage >= 80 else "❌"
            print(f"{status} {table:<37} {total:>10,} {normalized:>12,} {unnormalized:>10,} {coverage:>9.1f}%")
            state_total += total
            state_normalized += normalized
        except Exception as e:
            print(f"❌ {table:<37} Error: {e}")
            conn.rollback()

    state_coverage = (state_normalized / state_total * 100) if state_total > 0 else 0
    print("-" * 100)
    print(f"{'TOTAL':<40} {state_total:>10,} {state_normalized:>12,} {state_total-state_normalized:>10,} {state_coverage:>9.1f}%")
    print()

    # City coverage
    print("🏙️  CITY NORMALIZATION")
    print("-" * 100)
    print(f"{'Table':<40} {'Total':>10} {'Normalized':>12} {'Missing':>10} {'Coverage':>10}")
    print("-" * 100)

    city_tables = [
        ('jobs', 'city_id', 'city'),
    ]

    city_total = 0
    city_normalized = 0

    for table, id_col, name_col in city_tables:
        try:
            total, normalized, unnormalized, coverage = get_coverage(cursor, table, id_col, name_col)
            status = "✅" if coverage >= 95 else "⚠️ " if coverage >= 80 else "❌"
            print(f"{status} {table:<37} {total:>10,} {normalized:>12,} {unnormalized:>10,} {coverage:>9.1f}%")
            city_total += total
            city_normalized += normalized
        except Exception as e:
            print(f"❌ {table:<37} Error: {e}")
            conn.rollback()

    city_coverage = (city_normalized / city_total * 100) if city_total > 0 else 0
    print("-" * 100)
    print(f"{'TOTAL':<40} {city_total:>10,} {city_normalized:>12,} {city_total-city_normalized:>10,} {city_coverage:>9.1f}%")
    print()

    # Summary
    print("=" * 100)
    print("📊 OVERALL SUMMARY")
    print("=" * 100)
    print(f"🏢 Organizations: {org_coverage:>6.1f}% ({org_normalized:,}/{org_total:,})")
    print(f"🌍 Countries:     {country_coverage:>6.1f}% ({country_normalized:,}/{country_total:,})")
    print(f"🏛️  States:        {state_coverage:>6.1f}% ({state_normalized:,}/{state_total:,})")
    print(f"🏙️  Cities:        {city_coverage:>6.1f}% ({city_normalized:,}/{city_total:,})")
    print("=" * 100)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
