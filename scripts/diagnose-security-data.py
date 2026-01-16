#!/usr/bin/env python3
"""Diagnose security data - print all queries"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "91.98.158.19"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("=== FASE 1: DIAGNOSTICO ===\n")

# Total eventos
print("1. Total eventos:")
cur.execute("SELECT COUNT(*) FROM sofia.security_events")
print(f"   COUNT: {cur.fetchone()[0]}\n")

# Última data
print("2. Última data:")
cur.execute("SELECT MAX(event_date) FROM sofia.security_events")
max_date = cur.fetchone()[0]
print(f"   MAX(event_date): {max_date}\n")

# Eventos últimos 90 dias baseado em MAX
print("3. Eventos últimos 90 dias (baseado em MAX, não NOW):")
cur.execute("""
WITH maxd AS (SELECT MAX(event_date) AS d FROM sofia.security_events)
SELECT COUNT(*)
FROM sofia.security_events e, maxd
WHERE e.event_date >= (maxd.d - INTERVAL '90 days')
""")
count_90d = cur.fetchone()[0]
print(f"   COUNT: {count_90d}\n")

# Eventos últimos 30 dias baseado em MAX
print("4. Eventos últimos 30 dias (baseado em MAX, não NOW):")
cur.execute("""
WITH maxd AS (SELECT MAX(event_date) AS d FROM sofia.security_events)
SELECT COUNT(*)
FROM sofia.security_events e, maxd
WHERE e.event_date >= (maxd.d - INTERVAL '30 days')
""")
count_30d = cur.fetchone()[0]
print(f"   COUNT: {count_30d}\n")

# Eventos últimos 30 dias baseado em CURRENT_DATE (o bug!)
print("5. Eventos últimos 30 dias (baseado em CURRENT_DATE - O BUG!):")
cur.execute("""
SELECT COUNT(*)
FROM sofia.security_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
""")
count_current = cur.fetchone()[0]
print(f"   COUNT: {count_current}")
cur.execute('SELECT CURRENT_DATE')
current_date = cur.fetchone()[0]
print(f"   ^ Este eh o bug! CURRENT_DATE={current_date} mas MAX(event_date)={max_date}\n")

# Check view definitions (materialized views use different system table)
print("6. Current materialized view definitions:")
cur.execute("""
SELECT schemaname, matviewname
FROM pg_matviews
WHERE schemaname = 'sofia' AND matviewname LIKE 'mv_security%'
ORDER BY matviewname
""")
views = cur.fetchall()
if views:
    for view in views:
        print(f"   - {view[1]}")
        # Count records in each view
        cur.execute(f"SELECT COUNT(*) FROM sofia.{view[1]}")
        count = cur.fetchone()[0]
        print(f"     Records: {count}")
else:
    print("   NO MATERIALIZED VIEWS FOUND!")

cur.close()
conn.close()

print("\n=== DIAGNOSTICO COMPLETO ===")
