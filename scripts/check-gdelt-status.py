
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_gdelt():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=os.getenv("POSTGRES_DB")
        )
        cur = conn.cursor()

        print("🌍 Checking GDELT Data Status...")
        print("==================================================")

        # distinct dates
        cur.execute("""
            SELECT event_date::date, count(*) 
            FROM sofia.gdelt_events 
            GROUP BY 1 
            ORDER BY 1 DESC 
            LIMIT 10;
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("❌ No GDELT data found in sofia.gdelt_events!")
        else:
            print(f"✅ Found {len(rows)} recent days with data:")
            for row in rows:
                print(f"   📅 {row[0]}: {row[1]} events")

        # total count
        cur.execute("SELECT count(*) FROM sofia.gdelt_events;")
        total = cur.fetchone()[0]
        print(f"\n📊 Total records in table: {total}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_gdelt()
