#!/usr/bin/env python3
"""
Add UNIQUE constraint to sofia.jobs table for (job_id, platform)
"""

import subprocess
import sys

def run_sql(sql):
    """Execute SQL command using psql"""
    cmd = [
        'psql',
        '-U', 'sofia',
        '-d', 'sofia_db',
        '-c', sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

# Check if constraint exists
success, stdout, stderr = run_sql("""
    SELECT constraint_name 
    FROM information_schema.table_constraints 
    WHERE table_schema = 'sofia' 
    AND table_name = 'jobs' 
    AND constraint_name = 'jobs_unique_job_platform';
""")

if not success:
    print(f"❌ Error checking constraint: {stderr}")
    sys.exit(1)

if 'jobs_unique_job_platform' in stdout:
    print("✅ Constraint 'jobs_unique_job_platform' already exists")
else:
    print("Adding UNIQUE constraint on (job_id, platform)...")
    success, stdout, stderr = run_sql("""
        ALTER TABLE sofia.jobs 
        ADD CONSTRAINT jobs_unique_job_platform 
        UNIQUE (job_id, platform);
    """)
    
    if success:
        print("✅ Constraint added successfully!")
    else:
        print(f"❌ Error adding constraint: {stderr}")
        sys.exit(1)

