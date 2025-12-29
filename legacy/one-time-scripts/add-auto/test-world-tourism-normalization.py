#!/usr/bin/env python3
"""
Test world-tourism normalization without API calls
"""
import sys
import psycopg2
sys.path.insert(0, 'scripts')
from shared.geo_helpers import normalize_location

# Database connection
DB_CONFIG = {
    'host': '91.98.158.19',
    'port': 5432,
    'user': 'sofia',
    'password': 'sofia123strong',
    'database': 'sofia_db'
}

def test_normalization():
    print("=" * 80)
    print("TESTING WORLD TOURISM NORMALIZATION")
    print("=" * 80)
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Database connected")
    print()

    # Test countries from world_tourism_data
    test_countries = ['USA', 'BRA', 'FRA', 'CHN', 'ITA', 'ESP', 'GBR', 'DEU']

    print("Testing normalization for sample countries:")
    print()

    for country_code in test_countries:
        try:
            location = normalize_location(conn, {'country': country_code})
            country_id = location['country_id']

            if country_id:
                print(f"  ✅ {country_code:5} → country_id={country_id}")
            else:
                print(f"  ❌ {country_code:5} → NOT FOUND")
        except Exception as e:
            print(f"  ❌ {country_code:5} → ERROR: {e}")

    print()

    # Test inserting a sample record
    print("Testing INSERT with normalization:")
    print()

    cursor = conn.cursor()

    try:
        # Simulate a record from World Bank API
        test_record = {
            'countryiso3code': 'USA',
            'country': {'value': 'United States'},
            'indicator_code': 'ST.INT.ARVL',
            'indicator_name': 'International tourism, number of arrivals',
            'category': 'arrivals',
            'unit': 'number',
            'date': '2023',
            'value': 1000000
        }

        country_code = test_record.get('countryiso3code')
        country_name = test_record.get('country', {}).get('value')

        # Normalize country
        location = normalize_location(conn, {'country': country_code or country_name})
        country_id = location['country_id']

        print(f"  Country: {country_name} ({country_code})")
        print(f"  Normalized country_id: {country_id}")
        print()

        # Test INSERT (with rollback)
        cursor.execute("""
            INSERT INTO sofia.world_tourism_data
            (indicator_code, indicator_name, category, country_code, country_name, country_id, year, value, unit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (indicator_code, country_code, year)
            DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
            RETURNING id, country_id
        """, (
            test_record['indicator_code'],
            test_record['indicator_name'],
            test_record['category'],
            country_code,
            country_name,
            country_id,
            int(test_record['date']),
            float(test_record['value']),
            test_record['unit']
        ))

        result = cursor.fetchone()
        print(f"  ✅ INSERT successful!")
        print(f"  Record ID: {result[0]}")
        print(f"  Stored country_id: {result[1]}")

        conn.rollback()  # Don't actually save test data
        print(f"  (Rolled back - test only)")

    except Exception as e:
        print(f"  ❌ INSERT failed: {e}")
        conn.rollback()

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ NORMALIZATION TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_normalization()
