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

def check_skills():
    load_env()
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )
    
    with conn.cursor() as cur:
        # Check jobs skills
        print("--- JOBS SKILLS ---")
        cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE skills IS NOT NULL")
        s1 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sofia.jobs WHERE skills_required IS NOT NULL")
        s2 = cur.fetchone()[0]
        print(f"Jobs with skills: {s1}")
        print(f"Jobs with skills_required: {s2}")
        
        if s1 > 0:
            cur.execute("SELECT skills FROM sofia.jobs WHERE skills IS NOT NULL LIMIT 3")
            print(f"Sample skills: {cur.fetchall()}")
        elif s2 > 0:
            cur.execute("SELECT skills_required FROM sofia.jobs WHERE skills_required IS NOT NULL LIMIT 3")
            print(f"Sample skills_required: {cur.fetchall()}")

        # Check papers keywords
        print("\n--- PAPERS KEYWORDS ---")
        cur.execute("SELECT COUNT(*) FROM sofia.research_papers WHERE keywords IS NOT NULL")
        p1 = cur.fetchone()[0]
        print(f"Papers with keywords: {p1}")
        if p1 > 0:
            cur.execute("SELECT keywords FROM sofia.research_papers WHERE keywords IS NOT NULL LIMIT 3")
            print(f"Sample keywords: {cur.fetchall()}")

    conn.close()

if __name__ == "__main__":
    check_skills()
