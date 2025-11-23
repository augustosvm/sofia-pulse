#!/usr/bin/env python3
"""
================================================================================
LATIN AMERICA INTELLIGENCE (CEPAL/ECLAC)
================================================================================
Sources: CEPAL, ECLAC
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
    report_lines.append("🌎 LATIN AMERICA INTELLIGENCE (CEPAL/ECLAC)")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # CEPAL LATAM Data
    report_lines.append("=" * 80)
    report_lines.append("📊 CEPAL - ECONOMIC DATA")
    report_lines.append("=" * 80)
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.cepal_latam_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Records: {count:,}")
        if count > 0:
            cur.execute("""
                SELECT country_name, indicator_name, value, year
                FROM sofia.cepal_latam_data
                WHERE value IS NOT NULL
                ORDER BY year DESC, value DESC
                LIMIT 25
            """)
            for country, ind, val, year in cur.fetchall():
                ind_str = ind[:30] if ind else "N/A"
                report_lines.append(f"  • {country}: {ind_str} = {float(val):,.2f} ({year})")
    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ CEPAL error: {e}")
    report_lines.append("")

    # CEPAL Femicide
    report_lines.append("=" * 80)
    report_lines.append("⚠️ CEPAL - FEMICIDE DATA")
    report_lines.append("=" * 80)
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.cepal_femicide")
        count = cur.fetchone()[0]
        report_lines.append(f"Records: {count:,}")
        if count > 0:
            cur.execute("""
                SELECT country_code, femicide_count, rate_per_100k, year
                FROM sofia.cepal_femicide
                WHERE femicide_count IS NOT NULL
                ORDER BY rate_per_100k DESC
                LIMIT 15
            """)
            for country, count_f, rate, year in cur.fetchall():
                report_lines.append(f"  • {country}: {count_f} femicides ({float(rate):.2f}/100k) ({year})")
    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Femicide error: {e}")
    report_lines.append("")

    report_lines.append("💡 LATAM INSIGHTS:")
    report_lines.append("• Largest tech markets: Brazil, Mexico, Argentina, Colombia")
    report_lines.append("• Fastest growing: Chile, Peru, Colombia")
    report_lines.append("• Challenges: Political instability, currency volatility")
    report_lines.append("• Opportunities: Young population, mobile-first, fintech boom")
    report_lines.append("")

    cur.close()
    conn.close()

    report_text = "\n".join(report_lines)
    print(report_text)
    with open("analytics/latam-intelligence.txt", 'w') as f:
        f.write(report_text)
    print("\n✅ Saved: latam-intelligence.txt")

if __name__ == "__main__":
    main()
