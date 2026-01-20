#!/usr/bin/env python3
"""Demonstrate Women & NGO Intelligence MVs with real data."""
import psycopg2
import psycopg2.extras
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
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    database=os.getenv("POSTGRES_DB", "sofia_db")
)

print("=" * 80)
print("WOMEN INTELLIGENCE (Violence Risk Proxy)")
print("=" * 80)

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("""
    SELECT 
        country_code, 
        violence_risk_score, 
        events_30d, 
        events_90d, 
        fatalities_90d,
        violence_tier, 
        data_scope,
        confidence
    FROM sofia.mv_women_intelligence_by_country 
    WHERE confidence > 0
    ORDER BY violence_risk_score DESC 
    LIMIT 10
""")
women_rows = cur.fetchall()

for row in women_rows:
    print(f"\n{row['country_code']}: {row['violence_tier'].upper()}")
    print(f"  Risk Score: {row['violence_risk_score']}")
    print(f"  Events (4w): {row['events_30d']}, (13w): {row['events_90d']}")
    print(f"  Fatalities (13w): {row['fatalities_90d']}")
    print(f"  Data Scope: {row['data_scope']}")
    print(f"  Confidence: {row['confidence']}")

print("\n" + "=" * 80)
print("NGO COVERAGE")
print("=" * 80)

cur.execute("""
    SELECT 
        country_code, 
        ngo_coverage_score, 
        ngo_signals_30d, 
        ngo_signals_90d, 
        sector_diversity,
        ngo_tier, 
        confidence
    FROM sofia.mv_ngo_coverage_by_country 
    WHERE confidence > 0
    ORDER BY ngo_coverage_score DESC 
    LIMIT 10
""")
ngo_rows = cur.fetchall()

for row in ngo_rows:
    print(f"\n{row['country_code']}: {row['ngo_tier'].upper()}")
    print(f"  Coverage Score: {row['ngo_coverage_score']}")
    print(f"  Signals (4w): {row['ngo_signals_30d']}, (13w): {row['ngo_signals_90d']}")
    print(f"  Sector Diversity: {row['sector_diversity']}")
    print(f"  Confidence: {row['confidence']}")

print("\n" + "=" * 80)
print("STATISTICS")
print("=" * 80)

cur.execute("SELECT COUNT(*) FROM sofia.mv_women_intelligence_by_country WHERE confidence > 0")
women_count = cur.fetchone()['count']
print(f"Women Intelligence: {women_count} countries with data")

cur.execute("SELECT COUNT(*) FROM sofia.mv_ngo_coverage_by_country WHERE confidence > 0")
ngo_count = cur.fetchone()['count']
print(f"NGO Coverage: {ngo_count} countries with data")

cur.execute("SELECT COUNT(*) FROM sofia.ngo_keyword_rules")
keyword_count = cur.fetchone()['count']
print(f"NGO Keywords: {keyword_count} rules")

cur.close()
conn.close()
