import psycopg2
import os
import sys
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
        # Fallback for dev environment if empty
        os.environ["POSTGRES_PASSWORD"] = "postgres" 

    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv("POSTGRES_DB", "sofia_db"),
        )
        conn.autocommit = True
        
        migration_file = Path(__file__).parent.parent / "sql" / "migrations" / "008_capital_analytics.sql"
        print(f"📂 Running migration: {migration_file.name}")
        
        if not migration_file.exists():
             print(f"❌ File not found: {migration_file}")
             return

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
