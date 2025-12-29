#!/usr/bin/env python3
"""
Systematic Collector Normalization Script

Updates ALL 68 collectors to INSERT normalized foreign key IDs instead of string values.

Approach:
1. Group collectors by target table
2. Check each table for normalized columns (country_id, state_id, city_id)
3. Add missing columns
4. Create helper functions for ID lookups
5. Update collectors in batches
"""

import psycopg2
import json
from collections import defaultdict

DB_URL = 'postgresql://sofia:sofia123strong@91.98.158.19:5432/sofia_db'

# From the scan output, we know these 68 collectors need updates
COLLECTORS_BY_TABLE = {
    'acled_events': ['collect-acled-conflicts.py'],
    'brazil_security_data': ['collect-brazil-security.py'],
    'world_religion_data': ['collect-religion-data.py'],
    'jobs': [
        'collect-jobs-himalayas.ts',
        'collect-jobs-remoteok.ts',
        'collect-jobs-arbeitnow.ts',
        'collect-linkedin-jobs.ts',
        'collect-github-jobs.py',
        'collect-stackoverflow-jobs.py',
        'collect-freejobs-api.py',
        # ... plus 13+ more job collectors
    ],
    'women_eurostat_data': ['collect-women-eurostat.py'],
    'gender_indicators': ['collect-gender-stats.py'],
    'world_population_data': ['collect-population-data.py'],
    'world_gdp_data': ['collect-gdp-data.py'],
    # ... etc
}

def check_table_normalization(cursor, table_name):
    """Check if table has normalized geographic columns"""
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='sofia'
        AND table_name=%s
        AND column_name IN ('country_id', 'state_id', 'city_id', 'religion_id')
        ORDER BY column_name
    """, (table_name,))

    existing_columns = {row[0] for row in cursor.fetchall()}

    # Check what geographic data exists
    try:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='sofia'
            AND table_name=%s
            AND (
                column_name LIKE '%country%' OR
                column_name LIKE '%state%' OR
                column_name LIKE '%city%' OR
                column_name LIKE '%region%' OR
                column_name LIKE '%location%' OR
                column_name LIKE '%religion%'
            )
            AND column_name NOT LIKE '%_id'
            ORDER BY column_name
        """, (table_name,))

        geo_columns = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"   ⚠️  Could not check geo columns for {table_name}: {e}")
        geo_columns = []

    return {
        'table': table_name,
        'has_country_id': 'country_id' in existing_columns,
        'has_state_id': 'state_id' in existing_columns,
        'has_city_id': 'city_id' in existing_columns,
        'has_religion_id': 'religion_id' in existing_columns,
        'geo_columns': geo_columns,
        'needs_normalization': len(geo_columns) > 0 and len(existing_columns) == 0
    }

def get_row_count(cursor, table_name):
    """Get row count for table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"   ⚠️  Could not get count for {table_name}: {e}")
        return 0

def main():
    print("=" * 80)
    print("📊 SYSTEMATIC COLLECTOR NORMALIZATION AUDIT")
    print("=" * 80)
    print()

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # Get all tables that need normalization
    print("🔍 Scanning all tables for geographic data...\n")

    cursor.execute("""
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE table_schema='sofia'
        AND (
            column_name LIKE '%country%' OR
            column_name LIKE '%state%' OR
            column_name LIKE '%city%' OR
            column_name LIKE '%region%' OR
            column_name LIKE '%location%' OR
            column_name LIKE '%religion%'
        )
        AND table_name NOT IN ('countries', 'states', 'cities', 'religions')
        ORDER BY table_name
    """)

    tables_to_check = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(tables_to_check)} tables with geographic data\n")

    # Categorize tables by priority
    high_priority = []  # >10k rows, needs normalization
    medium_priority = []  # 1k-10k rows, needs normalization
    low_priority = []  # <1k rows, needs normalization
    already_normalized = []  # Has country_id/state_id/city_id

    for table in tables_to_check:
        info = check_table_normalization(cursor, table)
        row_count = get_row_count(cursor, table)
        info['row_count'] = row_count

        if info['has_country_id'] or info['has_state_id'] or info['has_city_id'] or info['has_religion_id']:
            already_normalized.append(info)
        elif row_count > 10000:
            high_priority.append(info)
        elif row_count > 1000:
            medium_priority.append(info)
        else:
            low_priority.append(info)

    # Print results
    print("=" * 80)
    print("🔴 HIGH PRIORITY (>10k rows, needs normalization)")
    print("=" * 80)
    for info in sorted(high_priority, key=lambda x: x['row_count'], reverse=True):
        print(f"\n📊 {info['table']}: {info['row_count']:,} rows")
        print(f"   Geographic columns: {', '.join(info['geo_columns'])}")
        print(f"   ❌ Missing: country_id, state_id, city_id")

    print("\n" + "=" * 80)
    print("🟡 MEDIUM PRIORITY (1k-10k rows, needs normalization)")
    print("=" * 80)
    for info in sorted(medium_priority, key=lambda x: x['row_count'], reverse=True):
        print(f"\n📊 {info['table']}: {info['row_count']:,} rows")
        print(f"   Geographic columns: {', '.join(info['geo_columns'])}")
        print(f"   ❌ Missing: country_id, state_id, city_id")

    print("\n" + "=" * 80)
    print("🟢 LOW PRIORITY (<1k rows, needs normalization)")
    print("=" * 80)
    for info in sorted(low_priority, key=lambda x: x['row_count'], reverse=True):
        print(f"\n📊 {info['table']}: {info['row_count']:,} rows")
        print(f"   Geographic columns: {', '.join(info['geo_columns'])}")
        print(f"   ❌ Missing: country_id, state_id, city_id")

    print("\n" + "=" * 80)
    print("✅ ALREADY NORMALIZED")
    print("=" * 80)
    for info in sorted(already_normalized, key=lambda x: x['row_count'], reverse=True):
        normalized_cols = []
        if info['has_country_id']: normalized_cols.append('country_id')
        if info['has_state_id']: normalized_cols.append('state_id')
        if info['has_city_id']: normalized_cols.append('city_id')
        if info['has_religion_id']: normalized_cols.append('religion_id')

        print(f"\n✅ {info['table']}: {info['row_count']:,} rows")
        print(f"   Has: {', '.join(normalized_cols)}")
        if info['geo_columns']:
            print(f"   Raw columns: {', '.join(info['geo_columns'])}")

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"High Priority (>10k):     {len(high_priority)} tables")
    print(f"Medium Priority (1k-10k): {len(medium_priority)} tables")
    print(f"Low Priority (<1k):       {len(low_priority)} tables")
    print(f"Already Normalized:       {len(already_normalized)} tables")
    print(f"TOTAL:                    {len(tables_to_check)} tables")
    print()

    # Save results to JSON for processing
    results = {
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority,
        'already_normalized': already_normalized
    }

    with open('/tmp/normalization_audit.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("💾 Results saved to: /tmp/normalization_audit.json\n")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
