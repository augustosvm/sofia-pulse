#!/usr/bin/env python3
"""
ACLED Final Verification - Saves full report
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

report = []
report.append("="*70)
report.append("🌍 ACLED REGIONAL DATA - FINAL VERIFICATION")
report.append("="*70)

# Check regional data
report.append("\n📊 ACLED AGGREGATED REGIONAL:")
cursor.execute("SELECT COUNT(*), COUNT(DISTINCT country) FROM acled_aggregated.regional")
total, countries = cursor.fetchone()
report.append(f"   Total records: {total:,}")
report.append(f"   Total countries: {countries}")

cursor.execute("""
    SELECT region, COUNT(*) as records, COUNT(DISTINCT country) as countries
    FROM acled_aggregated.regional
    GROUP BY region
    ORDER BY region
""")
report.append("\n   By region:")
for row in cursor.fetchall():
    report.append(f"   • {row[0]}: {row[1]:,} records, {row[2]} countries")

# Check if Ukraine exists
cursor.execute("""
    SELECT region, COUNT(*) as records
    FROM acled_aggregated.regional
    WHERE country ILIKE '%ukraine%'
    GROUP BY region
""")
ukraine_data = cursor.fetchall()
if ukraine_data:
    report.append("\n✅ UKRAINE FOUND:")
    for row in ukraine_data:
        report.append(f"   • {row[0]}: {row[1]:,} records")
else:
    report.append("\n⚠️  UKRAINE NOT FOUND")

# Check Middle East
cursor.execute("""
    SELECT country, COUNT(*) as records
    FROM acled_aggregated.regional
    WHERE region = 'Middle East'
    GROUP BY country
    ORDER BY records DESC
    LIMIT 10
""")
report.append("\n📍 MIDDLE EAST - Top 10 countries:")
for row in cursor.fetchall():
    report.append(f"   • {row[0]}: {row[1]:,} records")

# Check Europe
cursor.execute("""
    SELECT country, COUNT(*) as records
    FROM acled_aggregated.regional
    WHERE region = 'Europe and Central Asia'
    GROUP BY country
    ORDER BY records DESC
    LIMIT 10
""")
report.append("\n🇪🇺 EUROPE - Top 10 countries:")
for row in cursor.fetchall():
    report.append(f"   • {row[0]}: {row[1]:,} records")

cursor.close()
conn.close()

report.append("\n" + "="*70)
report.append("✅ Verification complete!")
report.append("="*70)

# Print and save
full_report = "\n".join(report)
print(full_report)

# Save to file
output_file = Path(__file__).parent.parent / "acled-verification-report.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_report)

print(f"\n📄 Report saved to: {output_file}")
