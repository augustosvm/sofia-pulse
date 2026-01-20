import psycopg2
import os
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def check_country_tables():
    load_env()
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )
    with conn.cursor() as cur:
        # Check dim_country columns
        cur.execute("SELECT * FROM sofia.dim_country LIMIT 1")
        print("\ndim_country fields:", [desc[0] for desc in cur.description])
        print("dim_country sample:", cur.fetchone())

        # Check countries columns
        cur.execute("SELECT * FROM sofia.countries LIMIT 1")
        print("\ncountries fields:", [desc[0] for desc in cur.description])
        print("countries sample:", cur.fetchone())
            
    conn.close()

if __name__ == "__main__":
    check_country_tables()
