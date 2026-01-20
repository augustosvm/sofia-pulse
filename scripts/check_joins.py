import psycopg2
import os
import json
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def get_db():
    load_env()
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )

def main():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 1. Check security_observations columns
        print("\n--- security_observations columns ---")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='sofia' AND table_name='security_observations'")
        cols = [r[0] for r in cur.fetchall()]
        print(cols)
        
        # 2. Check join clinical_trials -> organizations
        print("\n--- Clinical Trials -> Organizations Join ---")
        cur.execute("""
            SELECT COUNT(*) 
            FROM sofia.clinical_trials t
            JOIN sofia.organizations o ON t.sponsor = o.name
        """)
        match_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sofia.clinical_trials")
        total = cur.fetchone()[0]
        print(f"Matches: {match_count} / {total} trials")

        # 3. Check industry_signals metadata keys
        print("\n--- Industry Signals Metadata Keys ---")
        cur.execute("SELECT DISTINCT jsonb_object_keys(metadata) FROM sofia.industry_signals LIMIT 10")
        for r in cur.fetchall():
            print(f"Key: {r[0]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
