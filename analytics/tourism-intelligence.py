#!/usr/bin/env python3
"""
================================================================================
TOURISM INTELLIGENCE
================================================================================
Sources: World Bank Tourism, UNWTO
================================================================================
"""

import os
import psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'sofia'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )

def main():
    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("✈️ TOURISM INTELLIGENCE")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.world_tourism_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Top tourist destinations
            cur.execute("""
                SELECT country_name, indicator_name, value, year
                FROM sofia.world_tourism_data
                WHERE LOWER(indicator_name) LIKE '%arrival%' OR LOWER(indicator_name) LIKE '%tourist%'
                ORDER BY value DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 TOP TOURIST DESTINATIONS:")
                report_lines.append("-" * 60)
                for country, ind, val, year in rows:
                    val_str = f"{val/1e6:.1f}M" if val >= 1e6 else f"{val:,.0f}"
                    report_lines.append(f"  • {country:<25} {val_str} arrivals ({year})")
                report_lines.append("")

            # Tourism revenue
            cur.execute("""
                SELECT country_name, indicator_name, value, year
                FROM sofia.world_tourism_data
                WHERE LOWER(indicator_name) LIKE '%receipt%' OR LOWER(indicator_name) LIKE '%revenue%' OR LOWER(indicator_name) LIKE '%expenditure%'
                ORDER BY value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("💰 TOURISM REVENUE:")
                report_lines.append("-" * 60)
                for country, ind, val, year in rows:
                    val_str = f"${val/1e9:.1f}B" if val >= 1e9 else f"${val/1e6:.0f}M"
                    report_lines.append(f"  • {country:<25} {val_str} ({year})")
                report_lines.append("")

            # All indicators
            cur.execute("""
                SELECT DISTINCT indicator_name, COUNT(*) as countries
                FROM sofia.world_tourism_data
                GROUP BY indicator_name
                ORDER BY countries DESC
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 AVAILABLE INDICATORS:")
                report_lines.append("-" * 60)
                for ind, countries in rows:
                    report_lines.append(f"  • {ind[:50]}: {countries} countries")
                report_lines.append("")

    except Exception as e:
        report_lines.append(f"⚠️ Tourism error: {e}")
    
    report_lines.append("")
    report_lines.append("💡 INSIGHTS:")
    report_lines.append("• High tourism = good for B2C tech, hospitality tech")
    report_lines.append("• Tourism recovery = economic recovery indicator")
    report_lines.append("• Digital nomad destinations overlap with tourism hubs")
    report_lines.append("")

    cur.close()
    conn.close()

    report_text = "\n".join(report_lines)
    print(report_text)
    with open("analytics/tourism-intelligence.txt", 'w') as f:
        f.write(report_text)
    print("\n✅ Saved: tourism-intelligence.txt")

if __name__ == "__main__":
    main()
