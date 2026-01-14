#!/usr/bin/env python3
"""
================================================================================
TRADE & AGRICULTURE INTELLIGENCE
================================================================================
Sources:
- ComexStat (Brazilian Trade - MDIC): Import/export data
- FAO (Food and Agriculture Organization): Agricultural indicators
================================================================================
"""

import os
import psycopg2
from datetime import datetime

def get_connection():
    from dotenv import load_dotenv
    load_dotenv()

    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB') or os.getenv('DB_NAME', 'sofia_db'),
        user=os.getenv('POSTGRES_USER') or os.getenv('DB_USER', 'sofia'),
        password=os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD', '')
    )

def main():
    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🌾 TRADE & AGRICULTURE INTELLIGENCE")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # ComexStat Trade (Brazil)
    report_lines.append("=" * 80)
    report_lines.append("🌐 COMEXSTAT - BRAZILIAN TRADE")
    report_lines.append("=" * 80)
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.comexstat_trade")
        count = cur.fetchone()[0]
        report_lines.append(f"Records: {count:,}")
        if count > 0:
            # Top exports
            cur.execute("""
                SELECT ncm_description, value_usd, period, country_name
                FROM sofia.comexstat_trade
                WHERE value_usd IS NOT NULL AND flow = 'export'
                ORDER BY value_usd DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("")
                report_lines.append("📤 TOP BRAZILIAN EXPORTS:")
                report_lines.append("-" * 60)
                for product, value, period, country in rows:
                    report_lines.append(f"  • {product[:40]} → {country}: ${float(value):,.0f} ({period})")

            # Top imports
            cur.execute("""
                SELECT ncm_description, value_usd, period, country_name
                FROM sofia.comexstat_trade
                WHERE value_usd IS NOT NULL AND flow = 'import'
                ORDER BY value_usd DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("")
                report_lines.append("📥 TOP BRAZILIAN IMPORTS:")
                report_lines.append("-" * 60)
                for product, value, period, country in rows:
                    report_lines.append(f"  • {product[:40]} ← {country}: ${float(value):,.0f} ({period})")
    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ ComexStat error: {e}")
    report_lines.append("")

    # FAO Agriculture
    report_lines.append("=" * 80)
    report_lines.append("🌾 FAO - AGRICULTURE")
    report_lines.append("=" * 80)
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.fao_agriculture_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Records: {count:,}")
        if count > 0:
            cur.execute("SELECT country_name, indicator_name, value, year FROM sofia.fao_agriculture_data WHERE value IS NOT NULL ORDER BY value DESC LIMIT 20")
            for country, ind, val, year in cur.fetchall():
                ind_str = ind[:30] if ind else "N/A"
                report_lines.append(f"  • {country}: {ind_str} = {float(val):,.2f} ({year})")
    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ FAO error: {e}")
    report_lines.append("")

    # Add insights section
    report_lines.append("=" * 80)
    report_lines.append("💡 TRADE & AGRICULTURE INSIGHTS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("FOR BUSINESS INTELLIGENCE:")
    report_lines.append("• Brazilian exports = Supply chain opportunities")
    report_lines.append("• Agricultural production = Food security & pricing trends")
    report_lines.append("• Trade balance = Economic stability indicators")
    report_lines.append("")

    cur.close()
    conn.close()

    report_text = "\n".join(report_lines)
    print(report_text)
    with open("analytics/trade-agriculture-intelligence.txt", 'w', encoding='utf-8') as f:
        f.write(report_text)
    print("\n✅ Saved: trade-agriculture-intelligence.txt")

if __name__ == "__main__":
    main()
