#!/usr/bin/env python3
"""
Batch Table Normalization Script

Normalizes ALL remaining tables with geographic data in one go.
Adds country_id columns and populates them from existing country_code/country_name data.
"""

import psycopg2
from typing import List, Tuple

DB_URL = 'postgresql://sofia:sofia123strong@91.98.158.19:5432/sofia_db'

# Tables to normalize (from audit)
HIGH_PRIORITY = [
    'acled_aggregated',  # 198k rows
    'socioeconomic_indicators',  # 95k rows
    'women_world_bank_data',  # 63k rows
    'who_health_data',  # 48k rows
    'world_tourism_data',  # 19k rows
]

MEDIUM_PRIORITY = [
    'world_drugs_data',  # 10k rows
    'space_industry',  # 6.2k rows
    'world_sports_data',  # 5.5k rows
    'fao_agriculture_data',  # 4.4k rows
    'women_ilo_data',  # 3.8k rows
    'world_security_data',  # 3.4k rows
    'cepal_latam_data',  # 3.4k rows
    'unicef_children_data',  # 3.1k rows
    'gdelt_events',  # 2.6k rows
    'port_traffic',  # 2.5k rows
    'central_banks_women_data',  # 2.2k rows
    'comexstat_trade',  # 1.6k rows
]

# Eurostat-specific country code mappings
EUROSTAT_MAPPINGS = {
    'EL': 'GR',  # Greece
    'UK': 'GB',  # United Kingdom
}

def get_country_columns(cursor, table_name: str) -> Tuple[List[str], List[str]]:
    """Get geographic and ID columns for a table"""
    try:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='sofia' AND table_name=%s
            AND (column_name LIKE '%country%' OR column_name LIKE '%region%')
            ORDER BY ordinal_position
        """, (table_name,))

        rows = cursor.fetchall()
        all_cols = [row[0] for row in rows if row and len(row) > 0]
        geo_cols = [c for c in all_cols if not c.endswith('_id')]
        id_cols = [c for c in all_cols if c.endswith('_id')]

        return geo_cols, id_cols
    except Exception as e:
        print(f'DEBUG: Error in get_country_columns for {table_name}: {e}')
        print(f'DEBUG: Query returned: {cursor.fetchall() if cursor.description else "NO RESULTS"}')
        raise

def normalize_table(conn, cursor, table_name: str) -> dict:
    """Normalize a single table"""
    result = {
        'table': table_name,
        'success': False,
        'rows_updated': 0,
        'coverage_pct': 0,
        'errors': []
    }

    try:
        print(f'\n{"=" * 80}')
        print(f'🔧 Normalizing: {table_name}')
        print(f'{"=" * 80}')

        # Get columns
        try:
            geo_cols, id_cols = get_country_columns(cursor, table_name)
        except Exception as e:
            print(f'   ❌ Error getting columns: {e}')
            raise
        print(f'📋 Geographic columns: {", ".join(geo_cols)}')
        print(f'   ID columns: {", ".join(id_cols) if id_cols else "NONE"}')

        # Get row count
        cursor.execute(f'SELECT COUNT(*) FROM sofia.{table_name}')
        result = cursor.fetchone()
        total_rows = result[0] if result else 0
        print(f'   Total rows: {total_rows:,}')

        if total_rows == 0:
            print('   ⚠️  Empty table, skipping')
            result['success'] = True
            return result

        # Add country_id if missing
        if 'country_id' not in id_cols:
            print('   ✅ Adding country_id column...')
            cursor.execute(f'ALTER TABLE sofia.{table_name} ADD COLUMN country_id INTEGER')
            conn.commit()
            print('      ✓ Column added')
        else:
            print('   ℹ️  country_id already exists')

        # Find which country column to use (prefer country_code, then country_name, then country)
        country_col = None
        for col in ['country_code', 'country_name', 'country']:
            if col in geo_cols:
                country_col = col
                break

        if not country_col:
            print('   ⚠️  No suitable country column found')
            result['errors'].append('No country column')
            result['success'] = True  # Not an error, just nothing to do
            return result

        print(f'   🔄 Using column: {country_col}')

        # Populate country_id
        rows_updated = 0

        # Strategy 1: ISO alpha2
        cursor.execute(f"""
            UPDATE sofia.{table_name} t
            SET country_id = c.id
            FROM sofia.countries c
            WHERE c.iso_alpha2 = t.{country_col}
            AND t.country_id IS NULL
        """)
        updated = cursor.rowcount
        rows_updated += updated
        conn.commit()
        if updated > 0:
            print(f'      ✓ Matched {updated:,} rows via ISO alpha2')

        # Strategy 2: ISO alpha3
        cursor.execute(f"""
            UPDATE sofia.{table_name} t
            SET country_id = c.id
            FROM sofia.countries c
            WHERE c.iso_alpha3 = t.{country_col}
            AND t.country_id IS NULL
        """)
        updated = cursor.rowcount
        rows_updated += updated
        conn.commit()
        if updated > 0:
            print(f'      ✓ Matched {updated:,} rows via ISO alpha3')

        # Strategy 3: Country name (case-insensitive)
        cursor.execute(f"""
            UPDATE sofia.{table_name} t
            SET country_id = c.id
            FROM sofia.countries c
            WHERE LOWER(c.common_name) = LOWER(t.{country_col})
            AND t.country_id IS NULL
        """)
        updated = cursor.rowcount
        rows_updated += updated
        conn.commit()
        if updated > 0:
            print(f'      ✓ Matched {updated:,} rows via country name')

        # Strategy 4: Eurostat-specific codes
        for old_code, new_code in EUROSTAT_MAPPINGS.items():
            cursor.execute(f"""
                UPDATE sofia.{table_name} t
                SET country_id = (SELECT id FROM sofia.countries WHERE iso_alpha2 = %s)
                WHERE t.{country_col} = %s
                AND t.country_id IS NULL
            """, (new_code, old_code))
            updated = cursor.rowcount
            if updated > 0:
                rows_updated += updated
                print(f'      ✓ Fixed {old_code} → {new_code}: {updated:,} rows')
                conn.commit()

        # Check coverage
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT({country_col}) as has_country,
                COUNT(country_id) as has_id,
                100.0 * COUNT(country_id) / NULLIF(COUNT({country_col}), 0) as coverage
            FROM sofia.{table_name}
        """)
        coverage_result = cursor.fetchone()
        if not coverage_result:
            print('   ⚠️  Could not get coverage stats')
            total, has_country, has_id, coverage = 0, 0, 0, 0
        else:
            total, has_country, has_id, coverage = coverage_result
            coverage = coverage or 0

        print(f'\n   📈 Coverage: {has_id:,}/{has_country:,} ({coverage:.1f}%)')

        # Show unmapped
        if has_id < has_country:
            cursor.execute(f"""
                SELECT {country_col}, COUNT(*)
                FROM sofia.{table_name}
                WHERE {country_col} IS NOT NULL AND country_id IS NULL
                GROUP BY {country_col}
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)
            unmapped = cursor.fetchall()
            if unmapped:
                print('   ⚠️  Unmapped values:')
                for val, count in unmapped:
                    print(f'      {val[:30]:30} - {count:,} rows')

        # Add constraint if not exists
        try:
            cursor.execute(f"""
                ALTER TABLE sofia.{table_name}
                ADD CONSTRAINT fk_{table_name}_country
                FOREIGN KEY (country_id) REFERENCES sofia.countries(id)
            """)
            conn.commit()
            print('   🔗 Foreign key constraint added')
        except Exception as e:
            if 'already exists' in str(e).lower():
                print('   ℹ️  Foreign key constraint already exists')
            else:
                print(f'   ⚠️  Could not add constraint: {e}')
            conn.rollback()

        result['success'] = True
        result['rows_updated'] = rows_updated
        result['coverage_pct'] = coverage

        print(f'\n   ✅ {table_name} normalized successfully!')

    except Exception as e:
        print(f'\n   ❌ Error normalizing {table_name}: {e}')
        result['errors'].append(str(e))
        conn.rollback()

    return result

def main():
    print('=' * 80)
    print('🚀 BATCH TABLE NORMALIZATION')
    print('=' * 80)
    print()

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    all_tables = HIGH_PRIORITY + MEDIUM_PRIORITY
    results = []

    print(f'📊 Processing {len(all_tables)} tables...')
    print()

    for table_name in all_tables:
        result = normalize_table(conn, cursor, table_name)
        results.append(result)

    # Summary
    print('\n' + '=' * 80)
    print('📊 NORMALIZATION SUMMARY')
    print('=' * 80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f'\n✅ Successful: {len(successful)}/{len(results)}')
    print(f'❌ Failed: {len(failed)}')

    if successful:
        print('\n📈 Coverage by table:')
        for r in sorted(successful, key=lambda x: x['coverage_pct'], reverse=True):
            if r['rows_updated'] > 0:
                print(f'   {r["table"]:40} {r["coverage_pct"]:6.1f}% ({r["rows_updated"]:,} rows)')

    if failed:
        print('\n❌ Failed tables:')
        for r in failed:
            print(f'   {r["table"]:40} {", ".join(r["errors"])}')

    print('\n' + '=' * 80)
    print('✅ Batch normalization complete!')
    print('=' * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
