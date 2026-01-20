import os
import asyncio
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def list_jobs_columns():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = await asyncpg.connect(db_url)
        print("Connected. Fetching columns for table 'jobs' in schema 'sofia'...")
        
        rows = await conn.fetch("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = 'jobs'
            ORDER BY ordinal_position;
        """)
        
        if not rows:
            print("No columns found for sofia.jobs")
        
        print("\nCOLUMNS found:")
        print(f"{'Column':<25} {'Type':<15} {'Max Length':<10}")
        print("-" * 50)
        for r in rows:
            print(f"{r['column_name']:<25} {r['data_type']:<15} {str(r['character_maximum_length']):<10}")

        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_jobs_columns())
