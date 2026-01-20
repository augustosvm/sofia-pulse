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

def check_jobs_org_column():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔍 Checking if 'organization_id' exists in sofia.jobs:")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
              AND table_name = 'jobs'
              AND column_name = 'organization_id';
        """)
        
        row = cur.fetchone()
        if row:
            print(f"✅ FOUND: {row[0]} ({row[1]})")
            
            # Check if it is populated
            cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE organization_id IS NOT NULL")
            populated = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM sofia.jobs")
            total = cur.fetchone()[0]
            print(f"   Populated: {populated} / {total} records.")
        else:
            print("❌ NOT FOUND: organization_id column does not exist in sofia.jobs.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_jobs_org_column()
