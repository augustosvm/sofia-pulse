#!/usr/bin/env python3
"""
Add UNIQUE constraint to sofia.jobs table for (job_id, platform)
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', 5432)),
    user=os.getenv('POSTGRES_USER', 'sofia'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB', 'sofia_db')
)

cur = conn.cursor()

try:
    # Check if constraint already exists
    cur.execute("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_schema = 'sofia' 
        AND table_name = 'jobs' 
        AND constraint_name = 'jobs_unique_job_platform'
    """)
    
    if cur.fetchone():
        print("✅ Constraint 'jobs_unique_job_platform' already exists")
    else:
        print("Adding UNIQUE constraint on (job_id, platform)...")
        cur.execute("""
            ALTER TABLE sofia.jobs 
            ADD CONSTRAINT jobs_unique_job_platform 
            UNIQUE (job_id, platform)
        """)
        conn.commit()
        print("✅ Constraint added successfully!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
