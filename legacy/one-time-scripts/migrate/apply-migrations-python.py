#!/usr/bin/env python3
"""
Apply database migrations using Python (avoids psql dependency)
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME', 'sofia_db'),
}

def apply_migration(filename, description):
    """Apply a single migration file"""
    print(f"📊 {description}...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(0)  # AUTOCOMMIT mode
        cur = conn.cursor()

        with open(filename, 'r') as f:
            sql = f.read()

        cur.execute(sql)

        print(f"✅ {description} - SUCCESS")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ {description} - FAILED")
        print(f"   Error: {e}")
        return False

def main():
    print("=" * 80)
    print("📊 APPLYING CITY MIGRATIONS (Python)")
    print("=" * 80)
    print()

    print("Target database:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Port: {DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")
    print()

    # Test connection
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("✅ Database connection successful")
        print()
    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")
        return 1

    # Apply migrations
    migrations = [
        ('migrations/008-add-city-column.sql', 'Migration 008: Add city column to funding_rounds'),
        ('migrations/009-add-countries-column-openalex.sql', 'Migration 009: Add countries column to openalex_papers'),
    ]

    success_count = 0
    for filename, description in migrations:
        if os.path.exists(filename):
            if apply_migration(filename, description):
                success_count += 1
        else:
            print(f"⚠️  Migration file not found: {filename}")

    print()
    print("=" * 80)
    if success_count == len(migrations):
        print("✅ ALL MIGRATIONS APPLIED SUCCESSFULLY")
    else:
        print(f"⚠️  {success_count}/{len(migrations)} migrations applied")
    print("=" * 80)
    print()
    print("New columns added:")
    print("  • sofia.funding_rounds.city (VARCHAR 200)")
    print("  • sofia.openalex_papers.countries (TEXT[])")
    print()
    print("Next steps:")
    print("  1. Update collectors to populate these columns")
    print("  2. Run analytics: bash run-mega-analytics.sh")
    print()

    return 0 if success_count == len(migrations) else 1

if __name__ == '__main__':
    exit(main())
