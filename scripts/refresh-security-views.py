#!/usr/bin/env python3
"""
Refresh Security Materialized Views
Run after ACLED data is collected to update maps
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print('❌ DATABASE_URL not set')
    sys.exit(1)

def main():
    print('🔄 Refreshing security materialized views...\n')

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Check current data
        print('📊 Checking current data in security_events table...')
        cur.execute("""
            SELECT
                COUNT(*) as total,
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lng,
                MAX(longitude) as max_lng,
                COUNT(DISTINCT country_code) as countries
            FROM sofia.security_events
        """)

        row = cur.fetchone()
        total, min_lat, max_lat, min_lng, max_lng, countries = row

        print(f'   Total events: {total}')
        print(f'   Countries: {countries}')
        print(f'   Lat range: {min_lat} to {max_lat}')
        print(f'   Lng range: {min_lng} to {max_lng}\n')

        if total == 0:
            print('⚠️  No data in security_events table!')
            print('   Run ACLED collector first\n')
            sys.exit(1)

        # Refresh views
        print('🔄 Refreshing materialized views...')
        cur.execute('SELECT sofia.refresh_security_views()')
        conn.commit()
        print('✅ Views refreshed!\n')

        # Check geo points
        cur.execute('SELECT COUNT(*) FROM sofia.mv_security_geo_points')
        geo_count = cur.fetchone()[0]
        print(f'📍 Geo points in view: {geo_count}\n')

        # Sample by region
        print('🌍 Sample countries by region:')
        cur.execute("""
            SELECT country_code, country_name, incidents, severity_norm, risk_level
            FROM sofia.mv_security_country_summary
            ORDER BY severity_norm DESC
            LIMIT 20
        """)

        rows = cur.fetchall()
        for i, (code, name, incidents, severity, risk) in enumerate(rows, 1):
            print(f'   {i}. {name} ({code}): {incidents} incidents, severity {severity}, {risk}')

        print('\n✅ Done! Refresh your map in the browser.')

    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
