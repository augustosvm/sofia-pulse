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

def check_caps_view():
    load_env()
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT COUNT(*) as count FROM sofia.mv_capital_analytics")
        cnt = cur.fetchone()['count']
        print(f"Total rows in view: {cnt}")
        
        if cnt > 0:
            cur.execute("SELECT * FROM sofia.mv_capital_analytics LIMIT 5")
            for row in cur.fetchall():
                print(row)
            
    conn.close()

if __name__ == "__main__":
    check_caps_view()
