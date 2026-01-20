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

def check_recent_matches():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Recent Job -> Organization Matches:")
        print("=" * 60)
        
        cur.execute("""
            SELECT j.company, o.name 
            FROM sofia.jobs j
            JOIN sofia.organizations o ON j.organization_id = o.id
            -- Filter for jobs that likely were just updated (hard to track without updated_at, but we can sample)
            -- Or just show some valid matches where strings differ slightly
            WHERE j.organization_id IS NOT NULL
            AND LOWER(j.company) != LOWER(o.name)
            LIMIT 10;
        """)
        
        rows = cur.fetchall()
        for r in rows:
            print(f"Job Company: '{r[0]}'  -->  Org Name: '{r[1]}'")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_recent_matches()
