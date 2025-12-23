import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_runs():
    print(f"🔧 Env Check:")
    print(f"   SOFIA_WPP_ENDPOINT: {os.getenv('SOFIA_WPP_ENDPOINT')}")
    print(f"   WHATSAPP_API_URL: {os.getenv('WHATSAPP_API_URL')}")
    print(f"   WHATSAPP_NUMBER: {os.getenv('WHATSAPP_NUMBER')}")
    print("-" * 60)

    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB')
        )
        cursor = conn.cursor()
        
        print("🔍 Inspecting 'sofia.collector_runs' schema...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = 'collector_runs';
        """)
        columns = cursor.fetchall()
        print(f"   Columns found: {len(columns)}")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")

        # Get recent runs (generic select)
        print("\n📊 Recent Rows (Raw):")
        cursor.execute("SELECT * FROM sofia.collector_runs ORDER BY started_at DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
        conn.close()

    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_runs()
