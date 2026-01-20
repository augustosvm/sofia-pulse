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

def check_constraints():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Checking constraints on sofia.jobs:")
        cur.execute("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'sofia' AND conrelid = 'sofia.jobs'::regclass;
        """)
        
        rows = cur.fetchall()
        for r in rows:
            print(f"Constraint: {r[0]} | Def: {r[1]}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_constraints()
