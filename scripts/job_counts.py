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

def check_job_counts():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Count by source
        print("📊 Jobs per Source:")
        print("-" * 40)
        cur.execute("""
            SELECT 
                COALESCE(
                    source, 
                    substring(source_url from 'https?://(?:www\.)?([^/]+)')
                ) as derived_source, 
                COUNT(*) 
            FROM sofia.jobs 
            GROUP BY derived_source 
            ORDER BY count DESC;
        """)
        
        rows = cur.fetchall()
        total = 0
        for source, count in rows:
            print(f"{source:<25} : {count:>5}")
            total += count
            
        print("-" * 40)
        print(f"{'TOTAL':<25} : {total:>5}")
        
        # Check for normalization status too since we are here
        cur.execute("""
            SELECT COUNT(*) FROM sofia.jobs WHERE city_id IS NOT NULL;
        """)
        normalized = cur.fetchone()[0]
        print(f"\n🌍 Normalized (Geo-ID): {normalized} / {total} ({normalized/total*100:.1f}%)")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_job_counts()
