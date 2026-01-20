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
        
        # Check authors columns
        print("\n--- authors columns ---")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='sofia' AND table_name='authors'")
        cols = [r[0] for r in cur.fetchall()]
        print(cols)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
