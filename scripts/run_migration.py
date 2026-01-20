import psycopg2
import os
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip()

def run_migration():
    load_env()
    
    # Check password
    if not os.getenv("POSTGRES_PASSWORD"):
        print("❌ Error: POSTGRES_PASSWORD not found in .env")
        return

    try:
        # Use explicit kwargs to avoid URI parsing issues
        conn = psycopg2.connect(
            host="91.98.158.19",
            port="5432",
            database="sofia_db",
            user="sofia",
            password="SofiaPulse2025Secure@DB"
        )
        conn.autocommit = True
        
        migration_file = Path(__file__).parent.parent / "sql" / "migrations" / "100_fix_jobs_and_normalization.sql"
        print(f"📂 Running migration: {migration_file}")
        
        with open(migration_file, 'r') as f:
            sql = f.read()
            
        with conn.cursor() as cur:
            cur.execute(sql)
            
        print("✅ Migration executed successfully.")
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
