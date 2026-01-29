#!/usr/bin/env python3
"""
Sofia Pulse - GA4 BigQuery Collector (Production-Grade + Wrapped)

Collects Google Analytics 4 events from BigQuery export and stores in Postgres.

Features:
- Incremental collection by date range
- Idempotent (deduplication via event_hash)
- Timeout protection (10 minutes max)
- Collector run tracking in sofia.collector_runs
- Auto-detects GA4 dataset
- Batch inserts with execute_values
- Production-grade logging
"""

import os
import sys
import subprocess

# Import original collector
sys.path.insert(0, os.path.dirname(__file__))
from utils.collector_wrapper import wrapped_collector

# Wrapper that calls the original GA4 collector script
@wrapped_collector('ga4', timeout_seconds=600)
def main():
    """
    Wrapped version of GA4 collector with timeout + tracking.
    
    Calls the original collect_ga4_bigquery.py and captures output.
    """
    script_path = os.path.join(os.path.dirname(__file__), 'collect_ga4_bigquery.py')
    
    # Get command-line args (pass through to original script)
    args = sys.argv[1:]
    cmd = ['python3', script_path] + args
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    # Run original script and capture output
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(script_path)
    )
    
    # Print output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    # Check for errors
    if result.returncode != 0:
        raise RuntimeError(f"GA4 collector failed with exit code {result.returncode}")
    
    # Parse output to extract inserted count
    inserted = 0
    for line in result.stdout.split('\n'):
        if 'Inserted to Postgres:' in line:
            try:
                inserted = int(line.split(':')[1].strip().split()[0])
            except:
                pass
    
    print(f"\n✅ Extracted count: {inserted} events inserted")
    return inserted

if __name__ == '__main__':
    main()
