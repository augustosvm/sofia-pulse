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
                SELECT country, indicator, value, year 
                FROM sofia.cepal_latam_data 
                ORDER BY year DESC, value DESC 
                LIMIT 25
            """)
            for country, ind, val, year in cur.fetchall():
                report_lines.append(f"  • {country}: {ind[:30]} = {val:,.2f} ({year})")
    except Exception as e:
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
                SELECT country, indicator, value, year 
                FROM sofia.cepal_femicide 
                ORDER BY value DESC 
                LIMIT 15
            """)
            for country, ind, val, year in cur.fetchall():
                report_lines.append(f"  • {country}: {ind[:30]} = {val:.2f} ({year})")
    except Exception as e:
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
