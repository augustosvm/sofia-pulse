#!/usr/bin/env python3
"""
Sofia Pulse - Technical Schema Audit
Purpose: Analyze existing tables/MVs and identify derivable metrics
"""

import psycopg2
import psycopg2.extras
import os
from pathlib import Path
from datetime import datetime

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )

def audit_schema():
    load_env()
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=" * 80)
    print("SOFIA PULSE - TECHNICAL SCHEMA AUDIT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # 1. List all tables in sofia schema
    print("\n## 1. BASE TABLES (sofia.*)")
    cur.execute("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns c 
                WHERE c.table_schema = 'sofia' AND c.table_name = t.table_name) as col_count
        FROM information_schema.tables t
        WHERE table_schema = 'sofia' 
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    for row in cur.fetchall():
        # Get row count
        try:
            cur.execute(f"SELECT COUNT(*) as cnt FROM sofia.{row['table_name']}")
            cnt = cur.fetchone()['cnt']
        except:
            cnt = "?"
        print(f"  - {row['table_name']}: {cnt} rows, {row['col_count']} cols")
    
    # 2. List all materialized views
    print("\n## 2. MATERIALIZED VIEWS (sofia.mv_*)")
    cur.execute("""
        SELECT matviewname as name
        FROM pg_matviews
        WHERE schemaname = 'sofia'
        ORDER BY matviewname
    """)
    mvs = cur.fetchall()
    for row in mvs:
        try:
            cur.execute(f"SELECT COUNT(*) as cnt FROM sofia.{row['name']}")
            cnt = cur.fetchone()['cnt']
        except:
            cnt = "?"
        print(f"  - {row['name']}: {cnt} rows")
    
    # 3. Key columns for derivation
    print("\n## 3. GEO-DERIVABLE TABLES (has country field)")
    cur.execute("""
        SELECT DISTINCT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'sofia'
          AND (column_name ILIKE '%country%' OR column_name ILIKE '%iso%')
        ORDER BY table_name
    """)
    for row in cur.fetchall():
        print(f"  - {row['table_name']}.{row['column_name']}")
    
    # 4. Date columns for momentum
    print("\n## 4. TIME-SERIES TABLES (has date field)")
    cur.execute("""
        SELECT DISTINCT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'sofia'
          AND data_type IN ('date', 'timestamp with time zone', 'timestamp without time zone')
          AND column_name NOT IN ('created_at', 'updated_at', 'collected_at')
        ORDER BY table_name
    """)
    for row in cur.fetchall():
        print(f"  - {row['table_name']}.{row['column_name']} ({row['data_type']})")
    
    # 5. Numeric columns for scoring
    print("\n## 5. SCORABLE COLUMNS (numeric)")
    cur.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'sofia'
          AND data_type IN ('integer', 'bigint', 'numeric', 'real', 'double precision')
          AND column_name NOT IN ('id')
          AND table_name NOT LIKE 'mv_%'
        ORDER BY table_name, column_name
        LIMIT 50
    """)
    for row in cur.fetchall():
        print(f"  - {row['table_name']}.{row['column_name']}")
    
    # 6. Coverage analysis
    print("\n## 6. COUNTRY COVERAGE BY TABLE")
    tables_with_geo = [
        ('funding_rounds', 'country_id'),
        ('jobs', 'country'),
        ('research_papers', 'author_countries'),
        ('security_observations', 'country_code'),
    ]
    for table, col in tables_with_geo:
        try:
            if 'countries' in col:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT c) as countries 
                    FROM sofia.{table}, UNNEST({col}) c 
                    WHERE {col} IS NOT NULL
                """)
            else:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT {col}) as countries 
                    FROM sofia.{table} 
                    WHERE {col} IS NOT NULL
                """)
            cnt = cur.fetchone()['countries']
            print(f"  - {table}: {cnt} unique countries")
        except Exception as e:
            print(f"  - {table}: ERROR - {e}")
    
    cur.close()
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    audit_schema()
