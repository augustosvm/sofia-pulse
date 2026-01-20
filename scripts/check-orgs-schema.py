import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": "91.98.158.19",
    "port": "5432",
    "database": "sofia_db",
    "user": "sofia",
    "password": "SofiaPulse2025Secure@DB"
}

def check_orgs():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
              AND table_name = 'organizations'
            ORDER BY ordinal_position;
        """)
        
        rows = cur.fetchall()
        if not rows:
            print("Table sofia.organizations NOT FOUND.")
        else:
            print("sofia.organizations columns:")
            for r in rows:
                print(f"  {r[0]}: {r[1]}")

        cur.execute("SELECT count(*) FROM sofia.organizations")
        print(f"\nTotal Organizations: {cur.fetchone()[0]}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_orgs()
