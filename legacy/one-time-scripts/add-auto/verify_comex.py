from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sofia.comexstat_trade")
    count = cur.fetchone()[0]
    print(f"✅ Total Records in sofia.comexstat_trade: {count}")
    
    if count > 0:
        cur.execute("SELECT ncm_code, flow, country_name, value_usd FROM sofia.comexstat_trade LIMIT 5")
        rows = cur.fetchall()
        print("\nSample Data:")
        for row in rows:
            print(f"  - {row}")
            
    conn.close()
except Exception as e:
    print(f"❌ Verification failed: {e}")
