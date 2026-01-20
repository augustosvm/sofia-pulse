import psycopg2
import os
from dotenv import load_dotenv
import sys

# Force UTF-8 for stdout if needed, but we will write to file mostly
sys.stdout.reconfigure(encoding='utf-8')

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
        
        with open('counts_clean.txt', 'w', encoding='utf-8') as f:
            f.write("JOBS PER SOURCE REPORT\n")
            f.write("=" * 40 + "\n")
            
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
                s_safe = str(source) if source else "Unknown"
                f.write(f"{s_safe:<30} : {count:>6}\n")
                total += count
                
            f.write("-" * 40 + "\n")
            f.write(f"{'TOTAL':<30} : {total:>6}\n\n")
            
            # Normalization stats
            cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE city_id IS NOT NULL")
            normalized = cur.fetchone()[0]
            f.write(f"Normalized (Geo-ID)            : {normalized:>6} / {total}\n")

        cur.close()
        conn.close()
        print("Done writing counts_clean.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_job_counts()
