import os
import psycopg2
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "sofia_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def refresh_views():
    try:
        print(f"Connecting to database {DB_NAME} at {DB_HOST}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Checking raw security_events count...")
        cur.execute("SELECT count(*) FROM sofia.security_events WHERE source = 'HDX_HAPI_ACLED';")
        count = cur.fetchone()[0]
        print(f"Total HDX ACLED events in DB: {count}")

        if count == 0:
            print("WARNING: No events found. Collector might still be running or failed.")
        
        print("Refreshing materialized view: sofia.mv_security_geo_points...")
        start_time = time.time()
        cur.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_geo_points;")
        print(f"Done in {time.time() - start_time:.2f}s")

        print("Refreshing materialized view: sofia.mv_security_country_summary...")
        start_time = time.time()
        cur.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_country_summary;")
        print(f"Done in {time.time() - start_time:.2f}s")
        
        # Verify View Counts
        cur.execute("SELECT count(*) FROM sofia.mv_security_geo_points;")
        points_count = cur.fetchone()[0]
        print(f"Points in Map View: {points_count}")

        cur.execute("SELECT count(*) FROM sofia.mv_security_country_summary;")
        country_count = cur.fetchone()[0]
        print(f"Countries in Summary View: {country_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"Error refreshing views: {e}")
        return False

if __name__ == "__main__":
    refresh_views()
