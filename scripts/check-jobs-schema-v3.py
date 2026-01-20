import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def list_jobs_columns():
    try:
        # Use explicit kwargs to avoid URI parsing issues with special chars in password
        conn = psycopg2.connect(
            host="91.98.158.19",
            port="5432",
            database="sofia_db",
            user="sofia",
            password="SofiaPulse2025Secure@DB"
        )
        cur = conn.cursor()
        print("Connected. Fetching columns for table 'jobs' in schema 'sofia'...")
        
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
              AND table_name = 'organizations'
            ORDER BY ordinal_position;
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("No limited VARCHAR columns found!")
        
        print("\nLIMITED COLUMNS (Need Fix):")
        print(f"{'Column':<25} {'Type':<15} {'Max Length':<10}")
        print("-" * 50)
        for r in rows:
            col, dtype, length = r
            print(f"{col:<25} {dtype:<15} {str(length):<10}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_jobs_columns()
