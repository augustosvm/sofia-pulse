import psycopg2
import os

DB_HOST = "91.98.158.19"
DB_NAME = "sofia_db"
DB_USER = "sofia"
DB_PASS = "SofiaPulse2025Secure@DB"
DB_PORT = "5432"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    print("Applying migration 005_security_map_views.sql...")
    
    with open('sql/migrations/005_security_map_views.sql', 'r') as f:
        sql = f.read()
        cur.execute(sql)
        
    conn.commit()
    print("Migration applied successfully.")
    
    # Verify definition
    cur.execute("SELECT pg_get_viewdef('sofia.mv_security_geo_points')")
    definition = cur.fetchone()[0]
    if "ACLED_AGGREGATED" in definition:
        print("VERIFIED: ACLED_AGGREGATED is in the view definition.")
    else:
        print("WARNING: ACLED_AGGREGATED NOT found in view definition!")
        
    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
