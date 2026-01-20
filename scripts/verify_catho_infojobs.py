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

def verify_counts():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Verifying New Collectors Data:")
        print("=" * 60)
        
        cur.execute("""
            SELECT source, COUNT(*) 
            FROM sofia.jobs 
            WHERE source IN ('catho', 'infojobs')
            GROUP BY source;
        """)
        
        rows = cur.fetchall()
        if not rows:
            print("❌ No data found yet for 'catho' or 'infojobs'.")
        else:
            for r in rows:
                print(f"✅ {r[0]}: {r[1]} jobs saved.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_counts()
