#!/usr/bin/env python3
"""
================================================================================
TRADE & AGRICULTURE INTELLIGENCE
================================================================================
Sources: WTO, FAO, UN SDG
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
    report_lines.append("🌾 TRADE & AGRICULTURE INTELLIGENCE")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # WTO Trade
    report_lines.append("=" * 80)
    report_lines.append("🌐 WTO - WORLD TRADE")
    report_lines.append("=" * 80)
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.wto_trade_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Records: {count:,}")
        if count > 0:
            cur.execute("SELECT reporter_name, indicator_name, value, year FROM sofia.wto_trade_data WHERE value IS NOT NULL ORDER BY value DESC LIMIT 20")
            for country, ind, val, year in cur.fetchall():
                ind_str = ind[:30] if ind else "N/A"
                report_lines.append(f"  • {country}: {ind_str} = {float(val):,.2f} ({year})")
    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ WTO error: {e}")
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

    # UN SDG
    report_lines.append("=" * 80)
    report_lines.append("🎯 UN SDG - SUSTAINABLE DEVELOPMENT GOALS")
    report_lines.append("=" * 80)
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.sdg_indicators")
        count = cur.fetchone()[0]
        report_lines.append(f"Records: {count:,}")
        if count > 0:
            cur.execute("SELECT geo_area_name, goal, indicator_name, value, time_period FROM sofia.sdg_indicators WHERE value IS NOT NULL ORDER BY time_period DESC LIMIT 20")
            for country, goal, ind, val, year in cur.fetchall():
                ind_str = ind[:25] if ind else "N/A"
                report_lines.append(f"  • {country} (SDG {goal}): {ind_str} = {float(val):.2f} ({year})")
    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ SDG error: {e}")
    report_lines.append("")

    cur.close()
    conn.close()

    report_text = "\n".join(report_lines)
    print(report_text)
    with open("analytics/trade-agriculture-intelligence.txt", 'w') as f:
        f.write(report_text)
    print("\n✅ Saved: trade-agriculture-intelligence.txt")

if __name__ == "__main__":
    main()
