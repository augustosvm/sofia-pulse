#!/usr/bin/env python3
"""
Check what data is actually in acled_aggregated.regional table
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', '91.98.158.19')),
    'port': os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'dbs_sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia'))
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 70)
print("ACLED AGGREGATED.REGIONAL TABLE CHECK")
print("=" * 70)

# Check if table exists
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'acled_aggregated'
        AND tablename = 'regional'
    )
""")
exists = cursor.fetchone()[0]

if not exists:
    print("\n❌ Table acled_aggregated.regional does NOT exist!")
    print("   Need to run: python3 scripts/collect-acled-aggregated-postgres-v3.py")
    cursor.close()
    conn.close()
    exit(1)

# Total records
cursor.execute("SELECT COUNT(*) FROM acled_aggregated.regional")
total = cursor.fetchone()[0]
print(f"\n📊 Total records in acled_aggregated.regional: {total:,}")

# Top countries
cursor.execute("""
    SELECT country, COUNT(*) as records
    FROM acled_aggregated.regional
    GROUP BY country
    ORDER BY COUNT(*) DESC
    LIMIT 50
""")

print(f"\n🌍 Top 50 countries in regional table:")
print(f"{'Country':<30} {'Records':>10}")
print("-" * 42)

key_countries = {
    'Ukraine', 'United States', 'Brazil', 'Mexico', 'Syria',
    'Yemen', 'Myanmar', 'Philippines', 'India', 'Russia'
}
found = set()

for row in cursor.fetchall():
    country, count = row
    print(f"{country:<30} {count:>10,}")
    if country in key_countries:
        found.add(country)

print(f"\n🔍 Key Countries Check:")
for country in sorted(key_countries):
    status = '✅' if country in found else '❌'
    print(f"  {status} {country}")

# Check dataset_slug distribution
cursor.execute("""
    SELECT dataset_slug, COUNT(*) as records
    FROM acled_aggregated.regional
    GROUP BY dataset_slug
    ORDER BY COUNT(*) DESC
""")

print(f"\n📦 Dataset Slugs (regions downloaded):")
rows = cursor.fetchall()
for row in rows:
    slug, count = row
    print(f"  {slug}: {count:,} records")

if len(rows) == 1 and 'africa' in rows[0][0].lower():
    print(f"\n⚠️  PROBLEM: Only Africa dataset found!")
    print(f"   Expected: us-canada, latin-america, middle-east, asia-pacific, africa, europe")
    print(f"   Action: Re-run collector: python3 scripts/collect-acled-aggregated-postgres-v3.py")

cursor.close()
conn.close()

print("\n" + "=" * 70)
