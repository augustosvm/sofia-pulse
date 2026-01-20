#!/usr/bin/env python3
"""
Quick check of what went wrong
"""
import os
import sys
from pathlib import Path
import psycopg2

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip()

load_env()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER", "sofia"),
    password=os.getenv("POSTGRES_PASSWORD", ""),
    database=os.getenv("POSTGRES_DB", "sofia_db"),
)
conn.autocommit = True
cursor = conn.cursor()

print("Checking tables...")

# Check acled_aggregated.regional
try:
    cursor.execute("SELECT COUNT(*) FROM acled_aggregated.regional")
    print(f"✅ acled_aggregated.regional: {cursor.fetchone()[0]:,} records")
except Exception as e:
    print(f"❌ acled_aggregated.regional: {e}")

# Check sofia.security_events
try:
    cursor.execute("SELECT COUNT(*) FROM sofia.security_events")
    print(f"✅ sofia.security_events: {cursor.fetchone()[0]:,} records")
except Exception as e:
    print(f"❌ sofia.security_events: {e}")

# Check sofia.countries
try:
    cursor.execute("SELECT COUNT(*) FROM sofia.countries")
    print(f"✅ sofia.countries: {cursor.fetchone()[0]:,} records")
except Exception as e:
    print(f"❌ sofia.countries: {e}")

cursor.close()
conn.close()
