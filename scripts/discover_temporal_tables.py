#!/usr/bin/env python3
"""
Discovery: Find all temporal tables/columns in schema sofia
Output CSV-style report for planning migration 017d
"""
import psycopg2
from psycopg2.extras import DictCursor
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
print("TEMPORAL TABLES DISCOVERY - schema sofia")
print("=" * 80)

# Find all tables with temporal columns
cur.execute("""
    SELECT 
        t.table_name,
        c.column_name,
        c.data_type,
        c.udt_name
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name
    WHERE t.table_schema = 'sofia'
      AND c.table_schema = 'sofia'
      AND (
          c.column_name IN ('week', 'week_date', 'date', 'day', 'month', 'published_at', 'created_at', 'event_date', 'ts')
          OR c.data_type IN ('timestamp without time zone', 'timestamp with time zone', 'date')
      )
      AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.column_name
""")

temporal_tables = {}
for row in cur.fetchall():
    table = row['table_name']
    if table not in temporal_tables:
        temporal_tables[table] = []
    temporal_tables[table].append({
        'column': row['column_name'],
        'type': row['data_type'],
        'udt': row['udt_name']
    })

print(f"\nFound {len(temporal_tables)} tables with temporal columns\n")

# Analyze each table
candidates = []
for table, columns in temporal_tables.items():
    week_cols = [c for c in columns if 'week' in c['column'].lower()]
    
    if week_cols:
        for col_info in week_cols:
            col = col_info['column']
            
            # Get row count
            try:
                cur.execute(f"SELECT COUNT(*) as cnt FROM sofia.{table}")
                row_count = cur.fetchone()['cnt']
            except:
                row_count = 0
            
            # Check alignment for week columns
            misaligned = 0
            distinct_weeks = 0
            try:
                cur.execute(f"""
                    SELECT 
                        COUNT(DISTINCT {col}) as distinct_weeks,
                        COUNT(*) FILTER (WHERE {col} <> date_trunc('week', {col})) as misaligned
                    FROM sofia.{table}
                    WHERE {col} IS NOT NULL
                    LIMIT 1
                """)
                result = cur.fetchone()
                distinct_weeks = result['distinct_weeks'] or 0
                misaligned = result['misaligned'] or 0
            except Exception as e:
                print(f"  Warning: Could not analyze {table}.{col}: {e}")
            
            candidates.append({
                'table': table,
                'column': col,
                'type': col_info['type'],
                'row_count': row_count,
                'distinct_weeks': distinct_weeks,
                'misaligned': misaligned,
                'needs_fix': misaligned > 0
            })

# Print report
print("TABLE,COLUMN,TYPE,ROWS,DISTINCT_WEEKS,MISALIGNED,NEEDS_FIX")
for c in sorted(candidates, key=lambda x: x['misaligned'], reverse=True):
    print(f"{c['table']},{c['column']},{c['type']},{c['row_count']},{c['distinct_weeks']},{c['misaligned']},{c['needs_fix']}")

print(f"\n{'=' * 80}")
print(f"SUMMARY: {len([c for c in candidates if c['needs_fix']])} tables need week_start fix")
print(f"{'=' * 80}")

cur.close()
conn.close()
