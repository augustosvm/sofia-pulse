#!/usr/bin/env python3
"""
Run organization duplicate cleanup migration
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def main():
    # Read migration file
    with open('migrations/049_cleanup_duplicate_organizations.sql', 'r') as f:
        sql = f.read()

    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

    # Enable output
    conn.set_session(autocommit=True)

    # Execute migration
    cursor = conn.cursor()

    # Enable notices
    conn.notices = []

    print("🚀 Running duplicate cleanup migration...")
    print()

    cursor.execute(sql)

    # Print notices
    for notice in conn.notices:
        print(notice.strip())

    cursor.close()
    conn.close()

    print()
    print("✅ Migration complete!")

if __name__ == '__main__':
    main()
