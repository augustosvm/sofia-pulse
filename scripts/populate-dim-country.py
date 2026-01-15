#!/usr/bin/env python3
"""
Populate dim_country table with ISO codes, continent, region, and centroids
Uses REST Countries API
"""

import os
import sys
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print('❌ DATABASE_URL not set')
    sys.exit(1)

def get_countries():
    """Fetch country data from REST Countries API"""
    url = "https://restcountries.com/v3.1/all"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def main():
    print('🌍 Populating dim_country table...\n')

    # Fetch country data
    print('📥 Fetching country data from REST Countries API...')
    countries = get_countries()
    print(f'   Found {len(countries)} countries\n')

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        inserted = 0
        skipped = 0

        for country in countries:
            try:
                # Extract data
                cca3 = country.get('cca3')  # ISO3
                cca2 = country.get('cca2')  # ISO2
                name = country.get('name', {}).get('common', 'Unknown')
                continent = country.get('continents', ['Unknown'])[0] if country.get('continents') else 'Unknown'
                region = country.get('region', 'Unknown')
                subregion = country.get('subregion', region)

                # Get centroid (latlng)
                latlng = country.get('latlng', [])
                centroid_lat = latlng[0] if len(latlng) > 0 else None
                centroid_lon = latlng[1] if len(latlng) > 1 else None

                if not cca3:
                    skipped += 1
                    continue

                # Insert or update
                cur.execute("""
                    INSERT INTO sofia.dim_country
                    (country_code, country_name, iso2, iso3, continent, region, centroid_lat, centroid_lon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (country_code) DO UPDATE SET
                        country_name = EXCLUDED.country_name,
                        iso2 = EXCLUDED.iso2,
                        iso3 = EXCLUDED.iso3,
                        continent = EXCLUDED.continent,
                        region = EXCLUDED.region,
                        centroid_lat = EXCLUDED.centroid_lat,
                        centroid_lon = EXCLUDED.centroid_lon,
                        updated_at = NOW()
                """, (cca3, name, cca2, cca3, continent, subregion, centroid_lat, centroid_lon))

                inserted += 1

            except Exception as e:
                print(f'⚠️  Error processing {country.get("name", {}).get("common", "unknown")}: {e}')
                skipped += 1

        conn.commit()

        print(f'✅ Inserted/updated: {inserted}')
        print(f'⚠️  Skipped: {skipped}')

        # Show sample
        print('\n📊 Sample countries:')
        cur.execute("""
            SELECT country_code, country_name, continent, region, centroid_lat, centroid_lon
            FROM sofia.dim_country
            ORDER BY country_name
            LIMIT 10
        """)

        for row in cur.fetchall():
            code, name, cont, reg, lat, lon = row
            print(f'   {code}: {name} ({cont}, {reg}) @ {lat}, {lon}')

        print('\n✅ Done!')

    except Exception as e:
        conn.rollback()
        print(f'❌ Error: {e}')
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
