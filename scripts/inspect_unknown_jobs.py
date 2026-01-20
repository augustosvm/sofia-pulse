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

def inspect_unknown_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Analyzing 13,882 'Unknown' Records Quality:")
        print("=" * 60)
        
        # 1. Check for basic fields presence
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(title) as has_title,
                COUNT(description) as has_desc,
                COUNT(company) as has_company,
                COUNT(location) as has_loc,
                COUNT(published_at) as has_date
            FROM sofia.jobs 
            WHERE (LOWER(source) = 'unknown' OR source IS NULL) AND source_url IS NULL;
        """)
        
        stats = cur.fetchone()
        total = stats[0]
        print(f"Total Records Checked: {total}")
        print("-" * 30)
        print(f"Has Title       : {stats[1]} ({stats[1]/total*100:.1f}%)")
        print(f"Has Description : {stats[2]} ({stats[2]/total*100:.1f}%)")
        print(f"Has Company     : {stats[3]} ({stats[3]/total*100:.1f}%)")
        print(f"Has Location    : {stats[4]} ({stats[4]/total*100:.1f}%)")
        print(f"Has Date        : {stats[5]} ({stats[5]/total*100:.1f}%)")
        
        print("\n🔍 Sample Records (First 5):")
        print("-" * 60)
        
        cur.execute("""
            SELECT id, title, company, left(description, 50) as desc_preview, location, published_at
            FROM sofia.jobs 
            WHERE (LOWER(source) = 'unknown' OR source IS NULL) AND source_url IS NULL
            LIMIT 5;
        """)
        
        samples = cur.fetchall()
        for s in samples:
            print(f"ID: {s[0]}")
            print(f"Title: {s[1]}")
            print(f"Company: {s[2]}")
            print(f"Desc: {s[3]}...")
            print(f"Loc: {s[4]}")
            print(f"Date: {s[5]}")
            print("-" * 30)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_unknown_data()
