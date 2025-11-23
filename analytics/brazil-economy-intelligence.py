#!/usr/bin/env python3
"""
================================================================================
BRAZIL ECONOMY INTELLIGENCE
================================================================================
Comprehensive analysis of Brazilian economy using:
- BACEN SGS (Central Bank time series)
- IBGE (National statistics)
- IPEA (Applied economics research)
- ComexStat (Foreign trade)
- Brazil Ministries data

Indicators:
- Selic rate, inflation (IPCA), GDP growth
- Trade balance, exports/imports
- Employment, industry production
- Regional economic indicators
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
    print("=" * 80)
    print("🇧🇷 BRAZIL ECONOMY INTELLIGENCE")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🇧🇷 BRAZIL ECONOMY INTELLIGENCE")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # =========================================================================
    # 1. BACEN - Central Bank Data
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🏦 1. BANCO CENTRAL (BACEN SGS)")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.bacen_sgs_series")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Latest Selic, IPCA, Dollar
            cur.execute("""
                SELECT series_name, value, date, series_code
                FROM sofia.bacen_sgs_series
                WHERE series_code IN ('432', '433', '1', '4189')
                ORDER BY date DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 KEY INDICATORS (Latest):")
                report_lines.append("-" * 60)
                for name, value, date, code in rows:
                    indicator = {
                        '432': 'SELIC',
                        '433': 'IPCA',
                        '1': 'USD/BRL',
                        '4189': 'GDP Monthly'
                    }.get(code, name[:30])
                    report_lines.append(f"  • {indicator:<20} {value:>12.4f} ({date})")
                report_lines.append("")

            # All available series
            cur.execute("""
                SELECT DISTINCT series_name, series_code, COUNT(*) as records
                FROM sofia.bacen_sgs_series
                GROUP BY series_name, series_code
                ORDER BY records DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📋 AVAILABLE SERIES:")
                report_lines.append("-" * 60)
                for name, code, records in rows:
                    report_lines.append(f"  • {code}: {name[:45]} ({records} records)")
                report_lines.append("")

    except Exception as e:
        report_lines.append(f"⚠️ BACEN data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 2. IBGE - National Statistics
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("📊 2. IBGE - NATIONAL STATISTICS")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.ibge_indicators")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT indicator_name, value, location, period
                FROM sofia.ibge_indicators
                ORDER BY period DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 LATEST IBGE INDICATORS:")
                report_lines.append("-" * 60)
                for name, value, location, period in rows:
                    loc = location[:15] if location else "Brazil"
                    report_lines.append(f"  • {name[:35]}: {value:,.2f} ({loc}, {period})")
                report_lines.append("")

    except Exception as e:
        report_lines.append(f"⚠️ IBGE data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 3. IPEA - Economic Research
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("📈 3. IPEA - ECONOMIC RESEARCH")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.ipea_series")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT series_name, value, date, theme
                FROM sofia.ipea_series
                ORDER BY date DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 LATEST IPEA SERIES:")
                report_lines.append("-" * 60)
                for name, value, date, theme in rows:
                    theme_str = theme[:15] if theme else "General"
                    report_lines.append(f"  • {name[:35]}: {value:,.2f} ({theme_str}, {date})")
                report_lines.append("")

    except Exception as e:
        report_lines.append(f"⚠️ IPEA data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 4. ComexStat - Foreign Trade
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🚢 4. COMEXSTAT - FOREIGN TRADE")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.comexstat_trade")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Top exports
            cur.execute("""
                SELECT product, country, value_usd, flow, year
                FROM sofia.comexstat_trade
                WHERE LOWER(flow) LIKE '%export%'
                ORDER BY value_usd DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📤 TOP EXPORTS:")
                report_lines.append("-" * 60)
                for product, country, value, flow, year in rows:
                    value_str = f"${value/1e9:.2f}B" if value >= 1e9 else f"${value/1e6:.0f}M"
                    report_lines.append(f"  • {product[:30]} → {country[:15]}: {value_str} ({year})")
                report_lines.append("")

            # Top imports
            cur.execute("""
                SELECT product, country, value_usd, flow, year
                FROM sofia.comexstat_trade
                WHERE LOWER(flow) LIKE '%import%'
                ORDER BY value_usd DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📥 TOP IMPORTS:")
                report_lines.append("-" * 60)
                for product, country, value, flow, year in rows:
                    value_str = f"${value/1e9:.2f}B" if value >= 1e9 else f"${value/1e6:.0f}M"
                    report_lines.append(f"  • {product[:30]} ← {country[:15]}: {value_str} ({year})")
                report_lines.append("")

    except Exception as e:
        report_lines.append(f"⚠️ ComexStat data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 5. Brazil Ministries
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🏛️ 5. BRAZILIAN MINISTRIES DATA")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.brazil_ministries_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT ministry, indicator, value, year
                FROM sofia.brazil_ministries_data
                ORDER BY year DESC, value DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 MINISTRY INDICATORS:")
                report_lines.append("-" * 60)
                for ministry, indicator, value, year in rows:
                    report_lines.append(f"  • {ministry[:20]}: {indicator[:25]} = {value:,.2f} ({year})")
                report_lines.append("")

    except Exception as e:
        report_lines.append(f"⚠️ Ministries data error: {e}")
        report_lines.append("")

    # =========================================================================
    # INSIGHTS
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("💡 BRAZIL ECONOMY INSIGHTS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("KEY TAKEAWAYS:")
    report_lines.append("• Monitor SELIC for cost of capital decisions")
    report_lines.append("• Track USD/BRL for import/export planning")
    report_lines.append("• IPCA inflation impacts consumer purchasing power")
    report_lines.append("• Trade balance indicates export opportunities")
    report_lines.append("")
    report_lines.append("FOR TECH COMPANIES:")
    report_lines.append("• High Selic = harder to raise local funding")
    report_lines.append("• Weak BRL = good for USD-paid remote workers")
    report_lines.append("• Export tech services to earn USD")
    report_lines.append("• Monitor government tech spending via ministries")
    report_lines.append("")

    cur.close()
    conn.close()

    report_text = "\n".join(report_lines)
    print(report_text)

    output_path = "analytics/brazil-economy-intelligence.txt"
    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"\n✅ Report saved to: {output_path}")

if __name__ == "__main__":
    main()
