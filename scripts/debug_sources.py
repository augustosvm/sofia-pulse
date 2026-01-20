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

def debug_sources():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Inspecting jobs with Source = NULL or Unknown:")
        print("-" * 60)
        
        # Get sample of rows where source is null/empty
        cur.execute("""
            SELECT source, COUNT(*) 
            FROM sofia.jobs 
            GROUP BY source
            ORDER BY COUNT(*) DESC;
        """)
        
        rows = cur.fetchall()
        print(f"Total Source Groups: {len(rows)}")
        for r in rows:
            print(f"Source: '{r[0]}' | Count: {r[1]}")
        
        rows = cur.fetchall()
        if not rows:
            print("No unknown sources found (Raw query).")
        
        for r in rows:
            jid, src, url = r
            print(f"ID: {jid} | Source: {src} | URL: {url}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_sources()
