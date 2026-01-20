#!/usr/bin/env python3
"""
Data Quality: Week Alignment Health Check
Exit codes:
  0 - PASS (all weeks aligned)
  2 - FAIL (misaligned weeks detected)
  1 - ERROR (connection/execution failure)
"""
import psycopg2
from psycopg2.extras import DictCursor
import os
import sys
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def main():
    try:
        load_env()
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            dbname=os.getenv("POSTGRES_DB", "sofia_db"),
            connect_timeout=10,
            sslmode=os.getenv("POSTGRES_SSLMODE", "prefer")
        )
        
        cur = conn.cursor(cursor_factory=DictCursor)
        
        print("=" * 80)
        print("DATA QUALITY: Week Alignment Health Check")
        print("=" * 80)
        
        # Execute health check
        cur.execute("SELECT * FROM sofia.v_data_quality_week_alignment ORDER BY status DESC, distinct_weeks_not_aligned DESC")
        rows = cur.fetchall()
        
        if not rows:
            print("\nNo temporal tables found for monitoring")
            return 0
        
        # Print results
        print(f"\n{'Table':<25} {'Column':<15} {'Status':<8} {'Distinct Weeks':>15} {'Misaligned':>12} {'% Misaligned':>13}")
        print("-" * 80)
        
        failed_tables = []
        for row in rows:
            table = row['table_name']
            column = row['column_name']
            status = row['status']
            distinct_weeks = row['distinct_weeks']
            misaligned = row['distinct_weeks_not_aligned']
            pct = row['pct_distinct_not_aligned'] or 0
            
            status_icon = "PASS" if status == "PASS" else "FAIL"
            print(f"{table:<25} {column:<15} {status_icon:<8} {distinct_weeks:>15} {misaligned:>12} {pct:>12.2f}%")
            
            if status == "FAIL":
                failed_tables.append(f"{table}.{column}")
        
        print("=" * 80)
        
        # Summary
        total_checks = len(rows)
        passed =sum(1 for r in rows if r['status'] == 'PASS')
        failed = total_checks - passed
        
        print(f"\nSummary: {passed}/{total_checks} checks PASSED")
        
        if failed > 0:
            print(f"\nFAILED ({failed} tables):")
            for table in failed_tables:
                print(f"  - {table}")
            print("\nAction required: Run migration 017d to fix alignment")
            print("  psql -f sql/migrations/017d_week_start_standardization.sql")
            return 2
        else:
            print("\nAll temporal tables properly aligned")
            return 0
            
    except psycopg2.OperationalError as e:
        print(f"ERROR: Database connection failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Health check failed: {e}", file=sys.stderr)
        return 1
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
