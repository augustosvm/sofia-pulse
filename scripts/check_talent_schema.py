import psycopg2
import os
import psycopg2.extras
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def check_talent_schema():
    load_env()
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )
    
    tables = ['jobs', 'tech_jobs', 'research_papers', 'publications', 'organizations']
    
    with open('schema_dump.txt', 'w', encoding='utf-8') as f:
        with conn.cursor() as cur:
            for t in tables:
                f.write(f"\n--- Checking Table: sofia.{t} ---\n")
                try:
                    # Get columns
                    cur.execute(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'sofia' AND table_name = '{t}'
                    """)
                    cols = cur.fetchall()
                    if not cols:
                        f.write("Table not found or empty schema info.\n")
                        continue
                        
                    f.write(f"Columns: {[c[0] for c in cols]}\n")
                    
                    # Sample data
                    try:
                        cur.execute(f"SELECT * FROM sofia.{t} LIMIT 1")
                        row = cur.fetchone()
                        f.write(f"Sample: {row}\n")
                    except Exception as e:
                        f.write(f"Error sampling {t}: {e}\n")
                    
                    # Check count (approx)
                    # cur.execute(f"SELECT COUNT(*) FROM sofia.{t}")
                    # f.write(f"Count: {cur.fetchone()[0]}\n")
                    
                except Exception as e:
                    f.write(f"Error checking {t}: {e}\n")
                    conn.rollback()
            
    conn.close()
    print("Schema dumped to schema_dump.txt")

if __name__ == "__main__":
    check_talent_schema()
